import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import threading
import pyttsx3
import time
from collections import deque
import sys
import pythoncom  # Para inicializar COM en Windows
import keyboard  # Para detectar teclas (Push-to-Talk)
import torch
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
from voice_profile import VoiceProfile, get_default_profile_path

def trim_silence(audio_array, sample_rate=16000, silence_threshold_db=-40, min_silence_duration=0.3):
    """
    Recorta silencios al inicio y final del audio.

    Args:
        audio_array: Array de audio (numpy float32)
        sample_rate: Frecuencia de muestreo
        silence_threshold_db: Umbral de silencio en dB (ej: -40)
        min_silence_duration: Duración mínima de silencio para recortar (segundos)

    Returns:
        Audio recortado sin silencios en extremos
    """
    if len(audio_array) == 0:
        return audio_array

    # Convertir umbral de dB a amplitud lineal
    silence_threshold = 10 ** (silence_threshold_db / 20.0)

    # Calcular energía por frame (ventanas de 100ms)
    frame_length = int(sample_rate * 0.1)
    energy = np.array([
        np.sqrt(np.mean(audio_array[i:i+frame_length]**2))
        for i in range(0, len(audio_array) - frame_length, frame_length)
    ])

    # Encontrar inicio: primer frame con energía sobre el umbral
    start_idx = 0
    for i, e in enumerate(energy):
        if e > silence_threshold:
            start_idx = i * frame_length
            break

    # Encontrar fin: último frame con energía sobre el umbral
    end_idx = len(audio_array)
    for i in range(len(energy) - 1, -1, -1):
        if energy[i] > silence_threshold:
            end_idx = (i + 1) * frame_length
            break

    # Asegurar que no recortamos todo
    if start_idx >= end_idx:
        return audio_array

    return audio_array[start_idx:end_idx]


def normalize_audio_rms(audio_array, target_rms_db=-20):
    """
    Normaliza audio usando RMS (Root Mean Square) para volumen consistente.

    Args:
        audio_array: Array de audio (numpy float32)
        target_rms_db: RMS objetivo en dB (ej: -20)

    Returns:
        Audio normalizado
    """
    if len(audio_array) == 0:
        return audio_array

    # Calcular RMS actual
    rms = np.sqrt(np.mean(audio_array**2))

    if rms < 1e-10:  # Evitar división por cero (silencio completo)
        return audio_array

    # Convertir target de dB a lineal
    target_rms = 10 ** (target_rms_db / 20.0)

    # Calcular factor de ganancia
    gain = target_rms / rms

    # Limitar ganancia para evitar distorsión
    gain = min(gain, 10.0)  # Máximo +20dB

    # Aplicar ganancia
    normalized = audio_array * gain

    # Clip suave para evitar distorsión
    normalized = np.clip(normalized, -1.0, 1.0)

    return normalized


def load_audio_from_array(audio_array, sample_rate=16000,
                          apply_silence_trim=True, apply_normalization=True,
                          silence_threshold_db=-40, target_rms_db=-20):
    """
    Prepara array de audio para Whisper con mejoras de calidad.

    Args:
        audio_array: Array de audio desde sounddevice
        sample_rate: Frecuencia de muestreo
        apply_silence_trim: Si True, recorta silencios
        apply_normalization: Si True, normaliza con RMS
        silence_threshold_db: Umbral para detección de silencio
        target_rms_db: Nivel RMS objetivo

    Returns:
        Audio procesado listo para Whisper
    """
    # Asegurar que es float32
    audio_array = audio_array.astype(np.float32)

    # 1. Recortar silencios (mejora precisión de Whisper)
    if apply_silence_trim and len(audio_array) > sample_rate:  # Solo si >1 segundo
        audio_array = trim_silence(audio_array, sample_rate, silence_threshold_db)

    # 2. Normalización RMS (volumen consistente)
    if apply_normalization:
        audio_array = normalize_audio_rms(audio_array, target_rms_db)
    else:
        # Normalización básica por picos (fallback)
        max_val = np.abs(audio_array).max()
        if max_val > 1.0:
            audio_array = audio_array / max_val

    return audio_array


class RealtimeTranslator:
    def __init__(self, model_size="base", source_language="es", push_to_talk=False,
                 vad_enabled=True, vad_threshold=0.5, voice_profile=None):
        """
        Inicializa el traductor en tiempo real

        Args:
            model_size: Tamaño del modelo Whisper (tiny, base, small, medium, large)
            source_language: Idioma de origen (es para español)
            push_to_talk: Si True, solo graba mientras se mantiene presionada la barra espaciadora
            vad_enabled: Si True, usa Voice Activity Detection para filtrar ruido
            vad_threshold: Umbral de confianza VAD (0.0-1.0, recomendado: 0.5)
            voice_profile: Perfil de voz personalizado (VoiceProfile) o None
        """
        print("Inicializando traductor en tiempo real...")

        # Cargar modelo Whisper
        self.model = whisper.load_model(model_size)
        self.source_language = source_language
        self.push_to_talk = push_to_talk
        self.space_pressed = False  # Estado de la barra espaciadora

        # Configuración de audio
        self.sample_rate = 16000
        self.chunk_duration = 3  # Procesar cada 3 segundos (reducido de 5)
        self.chunk_samples = int(self.sample_rate * self.chunk_duration)

        # Perfil de voz personalizado
        self.voice_profile = voice_profile

        # Configuración de mejoras de audio
        self.vad_enabled = vad_enabled
        self.silence_threshold_db = -40  # Umbral para detección de silencio
        self.min_speech_duration = 0.5  # Segundos mínimos de voz para procesar

        # Aplicar configuración del perfil si existe
        if voice_profile and voice_profile.is_calibrated:
            print(f"✅ Cargando perfil de {voice_profile.user_name}")
            self.vad_threshold = voice_profile.vad_threshold
            self.target_rms_db = voice_profile.target_rms_db
            self.min_speech_duration = voice_profile.min_speech_duration
            voice_profile.update_usage_stats()
        else:
            # Valores por defecto si no hay perfil
            self.vad_threshold = vad_threshold
            self.target_rms_db = -20  # Nivel RMS objetivo para normalización

        # Cargar modelo VAD si está habilitado
        self.vad_model = None
        if self.vad_enabled:
            try:
                print("Cargando modelo Silero VAD...")
                self.vad_model = load_silero_vad()
                print("✓ VAD cargado exitosamente")
            except Exception as e:
                print(f"⚠️  No se pudo cargar VAD: {e}")
                print("Continuando sin VAD...")
                self.vad_enabled = False

        # Buffer de audio con overlap
        self.audio_queue = queue.Queue(maxsize=10)  # Limitar queue para evitar retraso
        self.tts_queue = queue.Queue()  # Cola separada para TTS
        self.buffer = deque(maxlen=self.chunk_samples * 2)

        # Motor TTS (inicializado en el thread de TTS)
        self.tts_voice_id = None

        # Seleccionar voz en inglés (hacerlo aquí para obtener el ID)
        temp_engine = pyttsx3.init()
        voices = temp_engine.getProperty('voices')

        # Buscar voz en inglés con mejor criterio
        english_voice = None
        for voice in voices:
            voice_name_lower = voice.name.lower()
            voice_id_lower = voice.id.lower()

            # Priorizar voces con "english", "david", "zira", "mark" (voces inglesas comunes en Windows)
            if any(keyword in voice_name_lower for keyword in ['english', 'zira', 'david', 'mark']):
                if 'spanish' not in voice_name_lower and 'español' not in voice_name_lower:
                    english_voice = voice
                    break

            # Backup: buscar por ID con "en-" o "en_"
            if ('en-' in voice_id_lower or 'en_' in voice_id_lower) and not english_voice:
                if 'spanish' not in voice_name_lower:
                    english_voice = voice

        if english_voice:
            self.tts_voice_id = english_voice.id
        else:
            # Si no encuentra voz en inglés, usar la primera disponible
            self.tts_voice_id = voices[0].id if voices else None

        temp_engine.stop()
        del temp_engine

        # Control de estado
        self.is_recording = False
        self.is_processing = False
        self.processing_lock = threading.Lock()

        # Contador de chunks procesados
        self.chunks_processed = 0
        self.translations_spoken = 0

        # Medición de tiempos (para optimización)
        self.show_timings = False  # Cambiar a True para ver tiempos detallados

        print("Traductor listo!\n")

    def has_speech(self, audio_chunk):
        """
        Detecta si un chunk de audio contiene voz humana usando Silero VAD.

        Args:
            audio_chunk: Array numpy con audio (float32)

        Returns:
            True si se detecta voz, False si es silencio/ruido
        """
        if not self.vad_enabled or self.vad_model is None:
            # Fallback: detección simple de energía
            audio_energy = np.abs(audio_chunk).mean()
            return audio_energy > 0.01

        try:
            # Convertir a tensor para Silero VAD
            audio_tensor = torch.from_numpy(audio_chunk).float()

            # Obtener timestamps de voz detectada
            speech_timestamps = get_speech_timestamps(
                audio_tensor,
                self.vad_model,
                threshold=self.vad_threshold,
                sampling_rate=self.sample_rate,
                min_speech_duration_ms=int(self.min_speech_duration * 1000),
                return_seconds=False
            )

            # Si hay al menos un segmento de voz detectado
            if len(speech_timestamps) > 0:
                # Calcular duración total de voz detectada
                total_speech_samples = sum(
                    [seg['end'] - seg['start'] for seg in speech_timestamps]
                )
                total_speech_duration = total_speech_samples / self.sample_rate

                # Verificar que haya suficiente voz
                return total_speech_duration >= self.min_speech_duration

            return False

        except Exception as e:
            # Si VAD falla, usar fallback de energía
            if self.show_timings:
                print(f"⚠️  VAD error (usando fallback): {e}")
            audio_energy = np.abs(audio_chunk).mean()
            return audio_energy > 0.01

    def audio_callback(self, indata, frames, time_info, status):
        """
        Callback para capturar audio del micrófono en tiempo real
        """
        if status:
            print(f"Estado de audio: {status}")

        # En modo Push-to-Talk, solo capturar si la barra espaciadora está presionada
        if self.push_to_talk and not self.space_pressed:
            return

        # Convertir audio a formato adecuado
        audio_data = indata.copy().flatten()

        # Agregar al buffer
        self.buffer.extend(audio_data)

        # En modo Push-to-Talk, NO procesar automáticamente
        # El procesamiento se hace al soltar la tecla
        if self.push_to_talk:
            return

        # MODO CONTINUO: Si tenemos suficiente audio, enviarlo a procesar
        if len(self.buffer) >= self.chunk_samples:
            # Extraer chunk del buffer
            chunk = np.array(list(self.buffer)[:self.chunk_samples])

            # Usar VAD mejorado para detectar voz (reemplaza threshold simple)
            if self.has_speech(chunk):
                try:
                    self.audio_queue.put(chunk, block=False)
                except queue.Full:
                    # Descartar el chunk más antiguo silenciosamente
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put(chunk, block=False)
                    except:
                        pass

            # Mantener overlap del 25% para continuidad
            overlap = self.chunk_samples // 4
            self.buffer = deque(
                list(self.buffer)[self.chunk_samples - overlap:],
                maxlen=self.chunk_samples * 2
            )
    
    def keyboard_listener(self):
        """
        Listener para detectar cuando se presiona/suelta la barra espaciadora
        """
        if not self.push_to_talk:
            return

        print("\n[Push-to-Talk] Mantén ESPACIO para hablar, suelta para procesar\n")

        def on_press():
            if not self.space_pressed:
                self.space_pressed = True
                # Limpiar buffer al empezar a grabar
                self.buffer.clear()
                print("🎤 Grabando... (mantén presionada la barra espaciadora)")

        def on_release():
            if self.space_pressed:
                self.space_pressed = False
                print("⏸️  Procesando...\n")

                # Procesar audio acumulado inmediatamente
                if len(self.buffer) > 0:
                    chunk = np.array(list(self.buffer))

                    # Verificar que tenga al menos 1 segundo de audio
                    if len(chunk) >= self.sample_rate:
                        # Usar VAD mejorado para validar que contiene voz
                        if self.has_speech(chunk):
                            try:
                                self.audio_queue.put(chunk, block=False)
                            except queue.Full:
                                try:
                                    self.audio_queue.get_nowait()
                                    self.audio_queue.put(chunk, block=False)
                                except:
                                    pass
                        else:
                            print("⚠️  No se detectó voz clara (solo ruido/silencio)\n")
                    else:
                        print("⚠️  Audio muy corto (min 1 segundo)\n")

                    # Limpiar buffer
                    self.buffer.clear()

        # Configurar hooks para la barra espaciadora
        keyboard.on_press_key('space', lambda _: on_press())
        keyboard.on_release_key('space', lambda _: on_release())

        # Mantener el listener activo
        while self.is_recording:
            time.sleep(0.1)

    def tts_worker(self):
        """
        Worker thread dedicado para Text-to-Speech (no bloqueante)
        Reinicia motor cada vez (más lento pero 100% confiable)
        """
        # Inicializar COM para este thread (necesario en Windows)
        try:
            pythoncom.CoInitialize()
        except Exception as e:
            print(f"Error al inicializar COM: {e}")
            return

        while self.is_recording:
            try:
                # Obtener texto para hablar
                text = self.tts_queue.get(timeout=1.0)

                if text:
                    # Crear motor NUEVO para cada reproducción (más confiable)
                    engine = None
                    try:
                        print(f"Reproduciendo...")

                        # Inicializar motor fresco
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 185)
                        engine.setProperty('volume', 1.0)

                        if self.tts_voice_id:
                            engine.setProperty('voice', self.tts_voice_id)

                        # Reproducir
                        engine.say(text)
                        engine.runAndWait()

                        self.translations_spoken += 1

                        # Limpiar motor inmediatamente
                        try:
                            engine.stop()
                        except:
                            pass

                        del engine
                        engine = None

                    except Exception as e:
                        print(f"Error al reproducir: {e}")

                        # Intentar limpiar
                        if engine:
                            try:
                                engine.stop()
                                del engine
                            except:
                                pass

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error en TTS: {e}")

        # Limpiar COM
        try:
            pythoncom.CoUninitialize()
        except:
            pass

    def process_audio_worker(self):
        """
        Worker thread que procesa chunks de audio continuamente
        """
        while self.is_recording:
            try:
                # Obtener chunk de audio (timeout de 1 segundo)
                audio_chunk = self.audio_queue.get(timeout=1.0)

                if not self.is_recording:
                    break

                self.chunks_processed += 1

                if self.show_timings:
                    total_start = time.time()

                print(f"\nEscuchando...")

                # Transcribir y traducir con Whisper
                try:
                    # Preparar audio con mejoras: silence trimming + RMS normalization
                    prep_start = time.time()

                    # Si hay perfil de voz, aplicar ajustes personalizados primero
                    if self.voice_profile and self.voice_profile.is_calibrated:
                        audio_chunk = self.voice_profile.apply_to_audio(audio_chunk, self.sample_rate)

                    audio_prepared = load_audio_from_array(
                        audio_chunk,
                        self.sample_rate,
                        apply_silence_trim=True,
                        apply_normalization=not (self.voice_profile and self.voice_profile.is_calibrated),  # Skip si profile ya normalizó
                        silence_threshold_db=self.silence_threshold_db,
                        target_rms_db=self.target_rms_db
                    )
                    prep_time = time.time() - prep_start

                    # Transcribir
                    whisper_start = time.time()
                    result = self.model.transcribe(
                        audio_prepared,
                        task="translate",
                        language=self.source_language,
                        fp16=False,
                        verbose=False,
                        # Optimizaciones para velocidad
                        beam_size=1,  # Reducir de 5 (por defecto) a 1 para mayor velocidad
                        best_of=1,    # Tomar solo la mejor opción
                        temperature=0  # Greedy decoding (más rápido)
                    )
                    whisper_time = time.time() - whisper_start

                    translated_text = result["text"].strip()

                    if translated_text:
                        print(f"→ {translated_text}")

                        if self.show_timings:
                            total_time = time.time() - total_start
                            print(f"⏱️  Prep: {prep_time*1000:.0f}ms | Whisper: {whisper_time*1000:.0f}ms | Total: {total_time*1000:.0f}ms")

                        # Enviar a TTS sin bloquear
                        self.tts_queue.put(translated_text)

                except Exception as e:
                    print(f"Error al procesar: {e}")

            except queue.Empty:
                # No hay audio en la cola, continuar esperando
                continue

            except Exception as e:
                print(f"Error: {e}")
    
    def start(self):
        """
        Inicia la captura y traducción en tiempo real
        """
        print("\n" + "="*60)
        print("TRADUCTOR EN TIEMPO REAL - ESPAÑOL → INGLÉS")
        print("="*60)

        if self.push_to_talk:
            print("\n🎮 MODO: Push-to-Talk")
            print("\nINSTRUCCIONES:")
            print("   • Mantén ESPACIO presionado para hablar")
            print("   • Suelta ESPACIO para procesar y traducir")
            print("   • Habla claramente en ESPAÑOL")
        else:
            print("\n🔄 MODO: Continuo")
            print("\nINSTRUCCIONES:")
            print("   • Habla claramente en ESPAÑOL")
            print("   • Haz pausas de 1-2 segundos entre frases")
            print(f"   • El sistema procesa cada {self.chunk_duration} segundos")

        print("   • La traducción se reproducirá automáticamente")
        print("\nPresiona Ctrl+C para detener\n")
        print("="*60)

        input("Presiona ENTER para comenzar...")

        self.is_recording = True

        # Iniciar thread de TTS
        tts_thread = threading.Thread(target=self.tts_worker)
        tts_thread.daemon = True
        tts_thread.start()

        # Iniciar thread de procesamiento
        processing_thread = threading.Thread(target=self.process_audio_worker)
        processing_thread.daemon = True
        processing_thread.start()

        # Iniciar keyboard listener si está en modo Push-to-Talk
        keyboard_thread = None
        if self.push_to_talk:
            keyboard_thread = threading.Thread(target=self.keyboard_listener)
            keyboard_thread.daemon = True
            keyboard_thread.start()
        
        try:
            # Iniciar captura de audio
            print("\n" + "="*60)
            if self.push_to_talk:
                print("LISTO - Presiona ESPACIO para hablar")
            else:
                print("GRABANDO - Empieza a hablar en español")
            print("="*60 + "\n")
            
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=int(self.sample_rate * 0.1)  # Bloques de 100ms
            ):
                # Mantener el programa corriendo
                while self.is_recording:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\nDeteniendo...")
        
        except Exception as e:
            print(f"\nError en captura de audio: {e}")
        
        finally:
            self.is_recording = False

            # Limpiar hooks del teclado si está en modo Push-to-Talk
            if self.push_to_talk:
                try:
                    keyboard.unhook_all()
                except:
                    pass

            # Esperar a que los threads terminen
            processing_thread.join(timeout=5)
            tts_thread.join(timeout=5)
            if keyboard_thread:
                keyboard_thread.join(timeout=2)

            print(f"\n{'='*60}")
            print(f"Sesión terminada")
            print(f"Traducciones: {self.translations_spoken}")
            print(f"{'='*60}")


def main():
    """
    Función principal
    """
    print("\n" + "="*60)
    print("TRADUCTOR DE VOZ EN TIEMPO REAL")
    print("Español → Inglés")
    print("="*60)

    # Configuración de modo
    print("\nMODO DE GRABACIÓN:")
    print("  1. Continuo (graba automáticamente)")
    print("  2. Push-to-Talk (mantén ESPACIO para hablar) 🎮")

    recording_mode = input("\nSelecciona (1-2, Enter=Continuo): ").strip()
    push_to_talk = (recording_mode == "2")

    # Configuración de modelo
    print("\nCALIDAD:")
    print("  1. Rápido   (Tiny, más veloz)")
    print("  2. Balanced (Base, recomendado) ⭐")
    print("  3. Preciso  (Small, mejor calidad)")

    mode_choice = input("\nSelecciona (1-3, Enter=Balanced): ").strip()

    # Configuración según modo
    if mode_choice == "1":
        model_size = "tiny"
    elif mode_choice == "3":
        model_size = "small"
    else:
        model_size = "base"

    # Opción para mostrar tiempos (debug)
    print("\n¿Mostrar tiempos de procesamiento? (para optimización)")
    show_timings_input = input("(s/n, Enter=No): ").strip().lower()
    show_timings = (show_timings_input == 's')

    # Crear traductor
    translator = RealtimeTranslator(
        model_size=model_size,
        source_language="es",
        push_to_talk=push_to_talk
    )

    # Configurar medición de tiempos
    translator.show_timings = show_timings

    # Iniciar
    try:
        translator.start()
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma terminado")
        sys.exit(0)