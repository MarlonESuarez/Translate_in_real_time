"""
Sistema de perfiles de voz personalizados
Analiza y guarda características únicas de la voz del usuario
para mejorar la precisión de transcripción
"""
import numpy as np
import json
import os
from datetime import datetime
from pathlib import Path
import soundfile as sf


class VoiceProfile:
    """
    Perfil personalizado de voz del usuario.
    Analiza características de audio y ajusta parámetros del sistema.
    """

    # 10 frases de calibración (cubren fonemas diversos del español)
    CALIBRATION_PHRASES = [
        "Hola, mi nombre es {user_name}",
        "Me gusta practicar inglés todos los días",
        "¿Qué hora es? Son las tres de la tarde",
        "El clima está muy agradable hoy",
        "Necesito comprar pan y leche en el supermercado",
        "Mi trabajo es muy interesante y desafiante",
        "Los números importantes son: cero, uno, cinco, diez, veinte",
        "Me encanta escuchar música mientras trabajo",
        "Voy a viajar a la playa este fin de semana",
        "Gracias por tu ayuda, hasta luego, pideme un favor"
    ]

    def __init__(self, user_name="Usuario", profile_path=None):
        """
        Inicializa perfil de voz.

        Args:
            user_name: Nombre del usuario
            profile_path: Ruta al archivo de perfil existente (para cargar)
        """
        self.user_name = user_name
        self.created_at = datetime.now().isoformat()
        self.version = "1.0"

        # Características de audio (valores por defecto)
        self.target_rms_db = -20.0  # RMS objetivo
        self.avg_pitch = 150.0  # Hz (pitch promedio)
        self.pitch_range = (80.0, 300.0)  # Hz (min, max)
        self.speaking_rate = 0.0  # sílabas/segundo (calculado)
        self.dynamic_range = 0.0  # dB (rango dinámico)
        self.avg_energy = 0.0  # Energía promedio

        # Configuración VAD personalizada
        self.vad_threshold = 0.5  # Default, se ajusta según voz
        self.min_speech_duration = 0.5  # segundos

        # Metadata de calibración
        self.calibration_data = []
        self.is_calibrated = False
        self.calibration_quality = 0.0  # 0-1

        # Estadísticas de uso
        self.sessions = 0
        self.total_translations = 0
        self.last_used = None

        # Cargar perfil si existe
        if profile_path and os.path.exists(profile_path):
            self.load(profile_path)

    def analyze_audio(self, audio_samples, sample_rate=16000, phrase_text=""):
        """
        Analiza un chunk de audio y extrae características.

        Args:
            audio_samples: Array numpy con audio (float32, mono)
            sample_rate: Frecuencia de muestreo (default: 16000)
            phrase_text: Texto de la frase (para metadata)

        Returns:
            dict con características extraídas
        """
        if len(audio_samples) == 0:
            return None

        # Asegurar que es float32 y 1D
        audio = audio_samples.astype(np.float32).flatten()

        # 1. RMS (Root Mean Square) - Nivel de volumen
        rms = np.sqrt(np.mean(audio ** 2))
        rms_db = 20 * np.log10(rms + 1e-10)  # Evitar log(0)

        # 2. Energía promedio
        energy = np.mean(np.abs(audio))

        # 3. Rango dinámico (diferencia entre pico y valle)
        peak = np.max(np.abs(audio))
        trough = np.min(np.abs(audio[np.abs(audio) > 0.01]))  # Ignorar silencio
        dynamic_range_db = 20 * np.log10((peak + 1e-10) / (trough + 1e-10))

        # 4. Pitch (frecuencia fundamental) usando autocorrelación
        pitch_hz = self._estimate_pitch(audio, sample_rate)

        # 5. Duración del audio
        duration = len(audio) / sample_rate

        # 6. Zero Crossing Rate (indicador de contenido de frecuencia)
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio)))) / 2
        zcr = zero_crossings / len(audio)

        characteristics = {
            "rms": rms,
            "rms_db": rms_db,
            "energy": energy,
            "dynamic_range_db": dynamic_range_db,
            "pitch_hz": pitch_hz,
            "duration": duration,
            "zero_crossing_rate": zcr,
            "sample_rate": sample_rate,
            "phrase_text": phrase_text,
            "quality_score": self._calculate_quality_score(rms, energy, duration)
        }

        return characteristics

    def _estimate_pitch(self, audio, sample_rate):
        """
        Estima pitch (F0) usando autocorrelación.

        Args:
            audio: Array de audio
            sample_rate: Frecuencia de muestreo

        Returns:
            Pitch estimado en Hz
        """
        # Rango de pitch esperado para voz humana: 80-400 Hz
        min_pitch = 80
        max_pitch = 400

        # Calcular autocorrelación
        correlation = np.correlate(audio, audio, mode='full')
        correlation = correlation[len(correlation) // 2:]

        # Encontrar pico en rango de pitch esperado
        min_period = int(sample_rate / max_pitch)
        max_period = int(sample_rate / min_pitch)

        if max_period >= len(correlation):
            return 150.0  # Default si no se puede calcular

        # Buscar máximo en rango válido
        peak_idx = np.argmax(correlation[min_period:max_period]) + min_period

        if peak_idx > 0:
            pitch = sample_rate / peak_idx
            return float(pitch)

        return 150.0  # Default

    def _calculate_quality_score(self, rms, energy, duration):
        """
        Calcula score de calidad de la muestra (0-1).

        Args:
            rms: Root Mean Square
            energy: Energía promedio
            duration: Duración en segundos

        Returns:
            Score entre 0 y 1
        """
        score = 1.0

        # Penalizar audio muy bajo
        if rms < 0.01:
            score *= 0.5

        # Penalizar audio muy corto
        if duration < 1.0:
            score *= 0.7

        # Penalizar energía muy baja
        if energy < 0.005:
            score *= 0.6

        # Recompensar duración adecuada (2-5 segundos)
        if 2.0 <= duration <= 5.0:
            score *= 1.2

        return min(score, 1.0)

    def add_calibration_sample(self, audio_samples, sample_rate=16000, phrase_id=0):
        """
        Agrega una muestra de calibración y la analiza.

        Args:
            audio_samples: Array con audio
            sample_rate: Frecuencia de muestreo
            phrase_id: ID de la frase (0-9)

        Returns:
            Características extraídas
        """
        phrase_text = self.CALIBRATION_PHRASES[phrase_id].format(
            user_name=self.user_name
        )

        characteristics = self.analyze_audio(audio_samples, sample_rate, phrase_text)

        if characteristics:
            characteristics["phrase_id"] = phrase_id
            self.calibration_data.append(characteristics)

        return characteristics

    def finalize_calibration(self):
        """
        Finaliza calibración y calcula parámetros optimizados.
        Se llama después de recolectar todas las muestras.

        Returns:
            bool - True si calibración exitosa
        """
        if len(self.calibration_data) < 5:
            print("⚠️  Necesitas al menos 5 frases para calibración")
            return False

        # Calcular promedios de todas las muestras
        all_rms_db = [s["rms_db"] for s in self.calibration_data]
        all_pitches = [s["pitch_hz"] for s in self.calibration_data if s["pitch_hz"] > 0]
        all_energies = [s["energy"] for s in self.calibration_data]
        all_dynamic_ranges = [s["dynamic_range_db"] for s in self.calibration_data]

        # 1. RMS objetivo (promedio del usuario)
        self.target_rms_db = np.mean(all_rms_db)

        # 2. Pitch promedio y rango
        if all_pitches:
            self.avg_pitch = np.mean(all_pitches)
            self.pitch_range = (
                max(np.min(all_pitches) - 20, 80),  # Min con margen
                min(np.max(all_pitches) + 20, 400)  # Max con margen
            )

        # 3. Rango dinámico promedio
        self.dynamic_range = np.mean(all_dynamic_ranges)

        # 4. Energía promedio
        self.avg_energy = np.mean(all_energies)

        # 5. Ajustar VAD threshold según energía del usuario
        # Si habla bajo, threshold más bajo; si habla fuerte, threshold más alto
        if self.avg_energy < 0.01:
            self.vad_threshold = 0.3  # Más sensible
        elif self.avg_energy > 0.05:
            self.vad_threshold = 0.6  # Menos sensible
        else:
            self.vad_threshold = 0.5  # Default

        # 6. Calcular calidad general de calibración
        quality_scores = [s["quality_score"] for s in self.calibration_data]
        self.calibration_quality = np.mean(quality_scores)

        # Marcar como calibrado
        self.is_calibrated = True
        self.created_at = datetime.now().isoformat()

        print(f"\n✅ Calibración completada:")
        print(f"   - RMS objetivo: {self.target_rms_db:.1f} dB")
        print(f"   - Pitch promedio: {self.avg_pitch:.0f} Hz")
        print(f"   - Rango pitch: {self.pitch_range[0]:.0f}-{self.pitch_range[1]:.0f} Hz")
        print(f"   - Threshold VAD: {self.vad_threshold:.2f}")
        print(f"   - Calidad: {self.calibration_quality*100:.0f}%")

        return True

    def apply_to_audio(self, audio_chunk, sample_rate=16000):
        """
        Aplica ajustes personalizados a un chunk de audio.

        Args:
            audio_chunk: Array numpy con audio
            sample_rate: Frecuencia de muestreo

        Returns:
            Audio ajustado
        """
        if not self.is_calibrated:
            return audio_chunk  # Sin cambios si no está calibrado

        audio = audio_chunk.astype(np.float32).flatten()

        # Normalización RMS personalizada
        current_rms = np.sqrt(np.mean(audio ** 2))

        if current_rms > 1e-10:  # Evitar división por cero
            # Calcular ganancia para alcanzar RMS objetivo
            target_rms_linear = 10 ** (self.target_rms_db / 20.0)
            gain = target_rms_linear / current_rms

            # Limitar ganancia para evitar distorsión
            gain = min(gain, 10.0)  # Máximo +20dB

            # Aplicar ganancia
            audio = audio * gain

            # Clip suave
            audio = np.clip(audio, -1.0, 1.0)

        return audio

    def save(self, filepath):
        """
        Guarda perfil a archivo JSON.

        Args:
            filepath: Ruta donde guardar el perfil
        """
        # Crear directorio si no existe
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Convertir tipos NumPy a tipos nativos de Python
        def convert_to_native(obj):
            """Convierte tipos NumPy a tipos nativos de Python"""
            if isinstance(obj, (np.integer, np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_native(item) for item in obj]
            return obj

        profile_data = {
            "user_name": self.user_name,
            "created_at": self.created_at,
            "version": self.version,
            "is_calibrated": self.is_calibrated,

            "audio_profile": {
                "target_rms_db": float(self.target_rms_db),
                "avg_pitch": float(self.avg_pitch),
                "pitch_range": [float(self.pitch_range[0]), float(self.pitch_range[1])],
                "speaking_rate": float(self.speaking_rate),
                "dynamic_range": float(self.dynamic_range),
                "avg_energy": float(self.avg_energy)
            },

            "vad_config": {
                "threshold": float(self.vad_threshold),
                "min_speech_duration": float(self.min_speech_duration)
            },

            "calibration_metadata": {
                "num_samples": len(self.calibration_data),
                "quality_score": float(self.calibration_quality),
                "samples": convert_to_native(self.calibration_data)
            },

            "usage_stats": {
                "sessions": int(self.sessions),
                "total_translations": int(self.total_translations),
                "last_used": self.last_used
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Perfil guardado en: {filepath}")

    def load(self, filepath):
        """
        Carga perfil desde archivo JSON.

        Args:
            filepath: Ruta del archivo de perfil
        """
        if not os.path.exists(filepath):
            print(f"⚠️  Archivo de perfil no encontrado: {filepath}")
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Información básica
            self.user_name = data.get("user_name", "Usuario")
            self.created_at = data.get("created_at", datetime.now().isoformat())
            self.version = data.get("version", "1.0")
            self.is_calibrated = data.get("is_calibrated", False)

            # Perfil de audio
            audio_profile = data.get("audio_profile", {})
            self.target_rms_db = audio_profile.get("target_rms_db", -20.0)
            self.avg_pitch = audio_profile.get("avg_pitch", 150.0)
            self.pitch_range = tuple(audio_profile.get("pitch_range", [80.0, 300.0]))
            self.speaking_rate = audio_profile.get("speaking_rate", 0.0)
            self.dynamic_range = audio_profile.get("dynamic_range", 0.0)
            self.avg_energy = audio_profile.get("avg_energy", 0.0)

            # Configuración VAD
            vad_config = data.get("vad_config", {})
            self.vad_threshold = vad_config.get("threshold", 0.5)
            self.min_speech_duration = vad_config.get("min_speech_duration", 0.5)

            # Metadata de calibración
            cal_meta = data.get("calibration_metadata", {})
            self.calibration_quality = cal_meta.get("quality_score", 0.0)
            self.calibration_data = cal_meta.get("samples", [])

            # Estadísticas
            stats = data.get("usage_stats", {})
            self.sessions = stats.get("sessions", 0)
            self.total_translations = stats.get("total_translations", 0)
            self.last_used = stats.get("last_used")

            print(f"✅ Perfil cargado: {self.user_name}")
            print(f"   - Calibrado: {'Sí' if self.is_calibrated else 'No'}")
            print(f"   - Calidad: {self.calibration_quality*100:.0f}%")

            return True

        except Exception as e:
            print(f"❌ Error al cargar perfil: {e}")
            return False

    def update_usage_stats(self):
        """Actualiza estadísticas de uso"""
        self.sessions += 1
        self.last_used = datetime.now().isoformat()

    def get_summary(self):
        """
        Retorna resumen del perfil como string.

        Returns:
            str con resumen del perfil
        """
        if not self.is_calibrated:
            return f"Perfil de {self.user_name} - No calibrado"

        summary = f"""
Perfil de Voz: {self.user_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Calibrado: Sí
Calidad: {self.calibration_quality*100:.0f}%
Muestras: {len(self.calibration_data)}

Características:
  • RMS: {self.target_rms_db:.1f} dB
  • Pitch: {self.avg_pitch:.0f} Hz ({self.pitch_range[0]:.0f}-{self.pitch_range[1]:.0f} Hz)
  • VAD: {self.vad_threshold:.2f}

Uso:
  • Sesiones: {self.sessions}
  • Traducciones: {self.total_translations}
"""
        return summary.strip()


def get_default_profile_path(user_name):
    """
    Retorna ruta por defecto para guardar perfil.

    Args:
        user_name: Nombre del usuario

    Returns:
        Path al archivo de perfil
    """
    # Crear directorio de perfiles si no existe
    profiles_dir = Path(__file__).parent / "voice_profiles"
    profiles_dir.mkdir(exist_ok=True)

    # Sanitizar nombre de usuario para nombre de archivo
    safe_name = "".join(c for c in user_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_').lower()

    return profiles_dir / f"{safe_name}_profile.json"
