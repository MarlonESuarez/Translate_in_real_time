"""
Script de prueba para Voice Activity Detection (VAD)
Graba 5 segundos de audio y muestra si se detecta voz
"""
import sounddevice as sd
import numpy as np
import torch
from silero_vad import load_silero_vad, get_speech_timestamps

def test_vad():
    print("="*60)
    print("TEST DE VOICE ACTIVITY DETECTION (VAD)")
    print("="*60)

    # Configuración
    sample_rate = 16000
    duration = 5  # segundos

    print("\n1. Cargando modelo Silero VAD...")
    try:
        vad_model = load_silero_vad()
        print("✓ VAD cargado exitosamente\n")
    except Exception as e:
        print(f"❌ Error al cargar VAD: {e}")
        return

    # Grabar audio
    print(f"2. Grabando {duration} segundos de audio...")
    print("   → Intenta hablar algo en español\n")

    input("Presiona ENTER para comenzar a grabar...")

    print("\n🎤 GRABANDO... (habla ahora)")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    print("✓ Grabación completada\n")

    # Procesar con VAD
    print("3. Analizando audio con VAD...")
    audio_array = audio.flatten()

    # Convertir a tensor
    audio_tensor = torch.from_numpy(audio_array).float()

    # Detectar voz
    try:
        speech_timestamps = get_speech_timestamps(
            audio_tensor,
            vad_model,
            threshold=0.5,
            sampling_rate=sample_rate,
            min_speech_duration_ms=500,
            return_seconds=True
        )

        print("\n" + "="*60)
        print("RESULTADOS DEL ANÁLISIS")
        print("="*60)

        if len(speech_timestamps) > 0:
            print(f"\n✅ VOZ DETECTADA - {len(speech_timestamps)} segmento(s)\n")

            total_speech_duration = 0
            for i, seg in enumerate(speech_timestamps, 1):
                duration_seg = seg['end'] - seg['start']
                total_speech_duration += duration_seg
                print(f"   Segmento {i}: {seg['start']:.2f}s - {seg['end']:.2f}s (duración: {duration_seg:.2f}s)")

            speech_percentage = (total_speech_duration / duration) * 100
            print(f"\n   Total de voz: {total_speech_duration:.2f}s ({speech_percentage:.1f}% del audio)")

            # Calcular energía de audio
            audio_energy = np.abs(audio_array).mean()
            audio_rms = np.sqrt(np.mean(audio_array**2))

            print(f"\n   Métricas de audio:")
            print(f"   - Energía promedio: {audio_energy:.6f}")
            print(f"   - RMS: {audio_rms:.6f}")

            if speech_percentage > 70:
                print("\n   🎯 EXCELENTE - Alta proporción de voz")
            elif speech_percentage > 40:
                print("\n   ✓ BUENO - Proporción aceptable de voz")
            else:
                print("\n   ⚠️  BAJO - Poca voz detectada (habla más cerca del micrófono)")
        else:
            print("\n❌ NO SE DETECTÓ VOZ")

            # Calcular energía para diagnóstico
            audio_energy = np.abs(audio_array).mean()
            print(f"\n   Energía de audio: {audio_energy:.6f}")

            if audio_energy < 0.001:
                print("   → Audio muy bajo (¿micrófono funcionando?)")
            elif audio_energy < 0.01:
                print("   → Audio débil (habla más fuerte o más cerca)")
            else:
                print("   → Audio presente pero VAD no detectó voz (posible ruido)")

            print("\n   Posibles causas:")
            print("   - Micrófono desconectado o silenciado")
            print("   - Volumen muy bajo")
            print("   - Solo ruido de fondo sin voz")
            print("   - Ambiente demasiado ruidoso")

    except Exception as e:
        print(f"\n❌ Error al procesar audio: {e}")

    print("\n" + "="*60)
    print("Test completado")
    print("="*60)


if __name__ == "__main__":
    try:
        test_vad()
    except KeyboardInterrupt:
        print("\n\nTest interrumpido")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
