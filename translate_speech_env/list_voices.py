"""
Script para listar todas las voces TTS disponibles en el sistema
"""
import pyttsx3

def list_all_voices():
    """Lista todas las voces disponibles con detalles"""
    print("\n" + "="*80)
    print("VOCES TTS DISPONIBLES EN EL SISTEMA")
    print("="*80 + "\n")

    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        if not voices:
            print("No se encontraron voces instaladas.")
            return

        print(f"Total de voces encontradas: {len(voices)}\n")

        english_voices = []
        spanish_voices = []
        other_voices = []

        for i, voice in enumerate(voices):
            voice_info = {
                'index': i,
                'name': voice.name,
                'id': voice.id,
                'languages': voice.languages if hasattr(voice, 'languages') else 'N/A',
                'gender': voice.gender if hasattr(voice, 'gender') else 'N/A',
                'age': voice.age if hasattr(voice, 'age') else 'N/A'
            }

            # Clasificar por idioma
            name_lower = voice.name.lower()
            id_lower = voice.id.lower()

            if any(kw in name_lower for kw in ['english', 'zira', 'david', 'mark']) or 'en-' in id_lower or 'en_' in id_lower:
                if 'spanish' not in name_lower:
                    english_voices.append(voice_info)
            elif 'spanish' in name_lower or 'español' in name_lower or 'helena' in name_lower or 'es-' in id_lower:
                spanish_voices.append(voice_info)
            else:
                other_voices.append(voice_info)

        # Mostrar voces en inglés
        if english_voices:
            print("🇺🇸 VOCES EN INGLÉS:")
            print("-" * 80)
            for v in english_voices:
                print(f"\n  [{v['index']}] {v['name']}")
                print(f"      ID: {v['id']}")
                print(f"      Idiomas: {v['languages']}")
                print(f"      Género: {v['gender']}")
                print(f"      Edad: {v['age']}")
        else:
            print("⚠ No se encontraron voces en inglés instaladas.")

        # Mostrar voces en español
        if spanish_voices:
            print("\n\n🇪🇸 VOCES EN ESPAÑOL:")
            print("-" * 80)
            for v in spanish_voices:
                print(f"\n  [{v['index']}] {v['name']}")
                print(f"      ID: {v['id']}")
                print(f"      Idiomas: {v['languages']}")
                print(f"      Género: {v['gender']}")

        # Mostrar otras voces
        if other_voices:
            print("\n\n🌍 OTRAS VOCES:")
            print("-" * 80)
            for v in other_voices:
                print(f"\n  [{v['index']}] {v['name']}")
                print(f"      ID: {v['id']}")
                print(f"      Idiomas: {v['languages']}")

        print("\n" + "="*80)
        print("\nRECOMENDACIÓNES:")
        print("-" * 80)

        if english_voices:
            print(f"✓ Para inglés, usa: {english_voices[0]['name']}")
        else:
            print("✗ NO hay voces en inglés instaladas.")
            print("\n  Para instalar voces en inglés en Windows:")
            print("  1. Configuración → Hora e idioma → Idioma")
            print("  2. Agregar idioma → English (United States)")
            print("  3. En Opciones de idioma → Descargar 'Texto a voz'")

        if spanish_voices:
            print(f"✓ Para español, usa: {spanish_voices[0]['name']}")

        engine.stop()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def test_voice(voice_index=None):
    """Prueba una voz específica"""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        if voice_index is None:
            print("\nPrueba de voz por defecto:")
            voice_to_use = voices[0]
        else:
            if voice_index < 0 or voice_index >= len(voices):
                print(f"Índice inválido. Debe estar entre 0 y {len(voices)-1}")
                return
            voice_to_use = voices[voice_index]

        print(f"\nProbando: {voice_to_use.name}")
        print("Reproduciendo mensaje de prueba...")

        engine.setProperty('voice', voice_to_use.id)
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)

        engine.say("Hello, this is a test message in English.")
        engine.runAndWait()

        print("✓ Reproducción completada\n")

        engine.stop()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_all_voices()

    print("\n" + "="*80)
    print("PRUEBA DE VOZ")
    print("="*80)

    try:
        choice = input("\n¿Quieres probar alguna voz? (ingresa número o Enter para salir): ").strip()

        if choice.isdigit():
            test_voice(int(choice))
        elif choice:
            print("Entrada inválida")

    except KeyboardInterrupt:
        print("\n\nSaliendo...")
