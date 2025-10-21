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

def load_audio_from_array(audio_array, sample_rate=16000):
    """
    Prepara array de audio para Whisper.
    El audio ya está en el formato correcto desde sounddevice.
    """
    # Asegurar que es float32
    audio_array = audio_array.astype(np.float32)

    # Normalizar si es necesario
    max_val = np.abs(audio_array).max()
    if max_val > 1.0:
        audio_array = audio_array / max_val

    return audio_array


class RealtimeTranslator:
    def __init__(self, model_size="base", source_language="es", push_to_talk=False):
        """
        Inicializa el traductor en tiempo real

        Args:
            model_size: Tamaño del modelo Whisper (tiny, base, small, medium, large)
            source_language: Idioma de origen (es para español)
            push_to_talk: Si True, solo graba mientras se mantiene presionada la barra espaciadora
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

            # Verificar si hay suficiente energía de audio (no es silencio)
            audio_energy = np.abs(chunk).mean()

            if audio_energy > 0.01:  # Umbral de silencio
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
                        audio_energy = np.abs(chunk).mean()

                        if audio_energy > 0.01:
                            try:
                                self.audio_queue.put(chunk, block=False)
                            except queue.Full:
                                try:
                                    self.audio_queue.get_nowait()
                                    self.audio_queue.put(chunk, block=False)
                                except:
                                    pass
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
                    # Preparar audio (sin necesidad de FFmpeg)
                    prep_start = time.time()
                    audio_prepared = load_audio_from_array(audio_chunk, self.sample_rate)
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