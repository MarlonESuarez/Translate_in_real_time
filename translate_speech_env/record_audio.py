import sounddevice as sd
import soundfile as sf
import numpy as np

def record_audio(duration=5, file_name="audio_prueba.wav"):
    """
    Graba audio desde el micrófono y lo guarda en un archivo WAV.
    
    Args:
        duration (int): Duración de la grabación en segundos.
        file_name (str): Nombre del archivo donde se guardará el audio.
    """

    print(f"Grabando audio por {duration} segundos...")
    print("Por favor, hable ahora.")
    print("Por ejemplo: 'Hola, ¿cómo estás?'")
    print("3... 2... 1... ¡Comenzando!")

    # Configuración de la grabación
    sample_rate = 16000  # Frecuencia de muestreo

    # Grabar el audio
    audio = sd.rec(
        int(duration * sample_rate), 
        samplerate=sample_rate, 
        channels=1, 
        dtype='float32'
    )
    sd.wait()  # Esperar a que termine la grabación

    # Guardar el audio en un archivo WAV
    sf.write(file_name, audio, sample_rate)
    print(f"Grabación completada. Audio guardado en '{file_name}'.")

    return file_name

if __name__ == "__main__":
    print("=" * 60)
    print("Bienvenido al grabador de audio")
    print("=" * 60)

    duration = input("Ingrese la duración de la grabación en segundos (por defecto 5): ")
    duration = int(duration) if duration else 5

    record_audio(duration)
    print("Proceso de grabación finalizado.")