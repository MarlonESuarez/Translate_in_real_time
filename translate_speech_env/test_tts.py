"""
Script de prueba para diagnosticar problemas de TTS
"""
import pyttsx3
import pythoncom
import threading
import time

def test_tts_main_thread():
    """Prueba TTS en el thread principal"""
    print("\n" + "="*60)
    print("TEST 1: TTS en thread principal")
    print("="*60)

    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)

        print("Reproduciendo: 'Hello, this is a test in the main thread'")
        engine.say("Hello, this is a test in the main thread")
        engine.runAndWait()
        print("✓ Test en thread principal: EXITOSO\n")
        return True
    except Exception as e:
        print(f"✗ Test en thread principal: FALLÓ - {e}\n")
        return False

def tts_worker_without_com():
    """TTS en thread secundario SIN inicializar COM"""
    print("Worker sin COM iniciado...")

    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)

        print("Reproduciendo: 'Test without COM initialization'")
        engine.say("Test without COM initialization")
        engine.runAndWait()
        print("✓ Reproducción completada\n")
    except Exception as e:
        print(f"✗ Error: {e}\n")

def tts_worker_with_com():
    """TTS en thread secundario CON inicializar COM"""
    print("Worker con COM iniciado...")

    try:
        # Inicializar COM
        pythoncom.CoInitialize()
        print("COM inicializado")

        engine = pyttsx3.init()
        engine.setProperty('rate', 150)

        print("Reproduciendo: 'Test with COM initialization'")
        engine.say("Test with COM initialization")
        engine.runAndWait()
        print("✓ Reproducción completada\n")

        # Limpiar COM
        pythoncom.CoUninitialize()
    except Exception as e:
        print(f"✗ Error: {e}\n")
        try:
            pythoncom.CoUninitialize()
        except:
            pass

def test_tts_thread_without_com():
    """Prueba TTS en thread secundario sin COM"""
    print("\n" + "="*60)
    print("TEST 2: TTS en thread secundario SIN COM")
    print("="*60)

    thread = threading.Thread(target=tts_worker_without_com)
    thread.start()
    thread.join()

def test_tts_thread_with_com():
    """Prueba TTS en thread secundario con COM"""
    print("\n" + "="*60)
    print("TEST 3: TTS en thread secundario CON COM")
    print("="*60)

    thread = threading.Thread(target=tts_worker_with_com)
    thread.start()
    thread.join()

def list_available_voices():
    """Lista las voces disponibles"""
    print("\n" + "="*60)
    print("VOCES DISPONIBLES")
    print("="*60)

    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        for i, voice in enumerate(voices):
            print(f"\n{i+1}. {voice.name}")
            print(f"   ID: {voice.id}")
            print(f"   Idiomas: {voice.languages}")

        engine.stop()
        print()
    except Exception as e:
        print(f"Error listando voces: {e}\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DIAGNÓSTICO DE TTS")
    print("="*60)
    print("\nEste script probará diferentes configuraciones de TTS")
    print("Escucha atentamente para determinar cuál funciona.\n")

    input("Presiona ENTER para comenzar...")

    # Listar voces
    list_available_voices()

    # Test 1: Thread principal
    test_tts_main_thread()
    time.sleep(1)

    # Test 2: Thread secundario sin COM
    test_tts_thread_without_com()
    time.sleep(1)

    # Test 3: Thread secundario con COM
    test_tts_thread_with_com()
    time.sleep(1)

    print("="*60)
    print("DIAGNÓSTICO COMPLETADO")
    print("="*60)
    print("\nResultados:")
    print("- Si escuchaste los 3 mensajes: TODO FUNCIONA ✓")
    print("- Si solo escuchaste el primero: Problema con threading")
    print("- Si solo escuchaste 1 y 3: COM es necesario (solución implementada)")
    print("- Si no escuchaste nada: Problema con el sistema de audio")
