import whisper
import pyttsx3
import os
import sys
import numpy as np
import soundfile as sf

# Cargar modelo Whisper para transcripción
print("Cargando modelo Whisper...")
model = whisper.load_model("base")
print("Modelo Whisper cargado.")

def list_files_of_audios(directory):
    """Lista todos los archivos de audio en el directorio"""
    extensiones = ('.wav', '.mp3', '.m4a', '.flac', '.ogg')
    archivos = []
    
    try:
        for archivo in os.listdir(directory):
            if archivo.lower().endswith(extensiones):
                ruta_completa = os.path.join(directory, archivo)
                tamaño = os.path.getsize(ruta_completa)
                archivos.append((archivo, ruta_completa, tamaño))
        return archivos
    except Exception as e:
        print(f"Error listando archivos: {e}")
        return []

def load_audio_with_soundfile(file_path):
    """
    Carga audio usando soundfile en lugar de FFmpeg.
    Retorna audio en el formato esperado por Whisper (16kHz, mono, float32).
    """
    try:
        # Leer el archivo de audio
        audio, sample_rate = sf.read(file_path, dtype='float32')

        # Convertir a mono si es estéreo
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        # Resamplear a 16kHz si es necesario
        if sample_rate != 16000:
            print(f"Nota: Remuestreando de {sample_rate}Hz a 16000Hz...")
            # Remuestreo simple usando interpolación lineal
            duration = len(audio) / sample_rate
            new_length = int(duration * 16000)
            audio = np.interp(
                np.linspace(0, len(audio), new_length),
                np.arange(len(audio)),
                audio
            )

        return audio
    except Exception as e:
        print(f"Error cargando audio con soundfile: {e}")
        raise

# Función para transcribir audio a texto
def transcribe_and_translate(file_audio):
    print("Transcribiendo y traduciendo audio...")

    try:
        # Cargar audio usando soundfile (sin necesidad de FFmpeg)
        print("Procesando archivo de audio...")
        audio_data = load_audio_with_soundfile(file_audio)

        # Transcribir el audio a inglés
        result = model.transcribe(
            audio_data,
            task='translate',  # Traducir a inglés
            language='es',     # Idioma fuente: español
            fp16=False,        # Desactivar FP16 para compatibilidad CPU
            verbose=False      # Reducir output de Whisper
        )

        original_text = result.get('text', '').strip()

        if original_text:
            print(f"\nTexto transcrito y traducido: {original_text}\n")
        else:
            print("Advertencia: No se detectó texto en el audio.")

        return original_text
    except Exception as e:
        print(f"\n*** Error durante la transcripción y traducción ***")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {e}")
        import traceback
        print("\nDetalles del error:")
        print(traceback.format_exc())
        return None

# Función para convertir texto a voz
def text_to_speech(text):
    print("Generando audio...")

    try:
        # Iniciando motor TTS
        engine = pyttsx3.init()

        # Configurar propiedades de la voz
        engine.setProperty('rate', 150)  # Velocidad de habla
        engine.setProperty('volume', 1.0)  # Volumen (0.0 a 1.0)

        # Obtener voces disponibles
        voices = engine.getProperty('voices')

        # Intentar usar una voz en inglés
        for voice in voices:
            if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break

        # Hablar el texto
        engine.say(text)
        engine.runAndWait()

        print("Audio reproducido!.")
    
    except Exception as e:
        print(f"Error en TTS: {e}")

# Funcion principal
def main():
    print("=" * 60)
    print("Bienvenido al traductor de voz (Español a Inglés)")
    print("=" * 60)

    # Directorio actual
    current_directory = os.getcwd()
    print(f"Listando archivos de audio en el directorio: {current_directory}")

    audio_files = list_files_of_audios(current_directory)

    if audio_files:
        print("Archivos de audio encontrados:")
        for idx, (nombre, ruta, tamaño) in enumerate(audio_files, start=1):
            print(f"{idx}. {nombre} - {tamaño / 1024:.2f} KB")

        print("0. Ingresar ruta de archivo manualmente")

        option = input("Seleccione un archivo por número o ingrese 0 para ruta manual: ")

        if option == '0':
            file = input("Ingrese la ruta completa del archivo de audio: ")
        elif option.isdigit() and 1 <= int(option) <= len(audio_files):
            file = audio_files[int(option) - 1][1]
        elif not option and audio_files:
            file = audio_files[0][1]
        else:
            print("Opción inválida. Saliendo.")
            return
    else:
        print("No se encontraron archivos de audio en el directorio actual.")
        file = input("Ingrese la ruta del archivo de audio: ")
    
    # Verificar si el archivo existe
    if not os.path.isfile(file):
        print(f"El archivo '{file}' no existe. Saliendo.")
        return
    
    # Verificar que el archivo no esté vacío
    size = os.path.getsize(file)
    if size == 0:
        print(f"El archivo '{file}' está vacío. Saliendo.")
        return
    
    print(f"Archivo seleccionado: {file} ({size / 1024:.2f} KB)")
    
    try:
        # Transcribir y traducir el audio
        translated_text = transcribe_and_translate(file)

        if translated_text:
            # Convertir el texto traducido a voz
            text_to_speech(translated_text)
            print("Proceso completado exitosamente.")
        else:
            print("No se pudo obtener texto traducido.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()