# 🎤 Traductor de Voz en Tiempo Real

Aplicación de traducción de voz en tiempo real de **Español → Inglés** con interfaz gráfica y modo terminal.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

---

## ✨ Características

### 🎯 Dos Interfaces
- **GUI (Interfaz Gráfica)** - Amigable y visual
- **CLI (Terminal)** - Rápida y ligera

### 🎮 Modos de Grabación
- **Continuo** - Graba automáticamente
- **Push-to-Talk** - Mantén ESPACIO para hablar

### ⚡ Optimizado para Velocidad
- Chunks de 3 segundos
- Motor TTS optimizado
- Parámetros Whisper ajustados
- Latencia: ~1-2 segundos

### 🎨 Calidades Disponibles
- **Rápido** (Tiny) - Más veloz
- **Balanced** (Base) - Recomendado ⭐
- **Preciso** (Small) - Mejor calidad

### 🎤 Mejoras de Calidad de Audio (NUEVO ⭐)
- **Silero VAD** - Detección inteligente de voz vs. ruido
- **Silence Trimming** - Elimina silencios automáticamente
- **RMS Normalization** - Volumen consistente
- **+20-30% precisión** en ambientes ruidosos
- **-30% latencia** (no procesa audio sin voz)

---

## 🚀 Inicio Rápido

### 1. Clonar Repositorio
```bash
git clone https://github.com/TU_USUARIO/Translate_v1.git
cd Translate_v1
```

### 2. Crear Entorno Virtual
```bash
python -m venv translate_speech_env
```

### 3. Activar Entorno Virtual

**Windows (PowerShell):**
```powershell
translate_speech_env\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
translate_speech_env\Scripts\activate.bat
```

### 4. Instalar Dependencias
```bash
pip install -r translate_speech_env/requirements.txt
```

### 5. Ejecutar

**Interfaz Gráfica (Recomendado):**
```bash
python translate_speech_env/translate_gui.py
```
O doble clic en: `translate_speech_env/run_gui.bat`

**Terminal:**
```bash
python translate_speech_env/translate_realtime.py
```

---

## 📦 Requisitos

### Software
- Python 3.11 o superior
- Windows 10/11
- Micrófono funcional
- Altavoces/Audífonos

### Dependencias Principales
- `openai-whisper` - Transcripción y traducción
- `pyttsx3` - Text-to-Speech
- `sounddevice` - Captura de audio
- `keyboard` - Detección de teclas (Push-to-Talk)
- `silero-vad` - Voice Activity Detection (NEW ⭐)
- `tkinter` - Interfaz gráfica (incluido con Python)

---

## 🎮 Uso

### Interfaz Gráfica (GUI)

1. **Ejecutar:**
   ```bash
   python translate_speech_env/translate_gui.py
   ```

2. **Configurar:**
   - Modo: Continuo / Push-to-Talk
   - Calidad: Rápido / Balanced / Preciso

3. **Clic en "▶ Iniciar"**

4. **Hablar:**
   - Continuo: Habla normalmente
   - Push-to-Talk: Mantén ESPACIO

5. **Ver traducciones en pantalla**

### Terminal (CLI)

1. **Ejecutar:**
   ```bash
   python translate_speech_env/translate_realtime.py
   ```

2. **Seguir menú interactivo**

3. **Hablar y escuchar traducciones**

---

## 📁 Estructura del Proyecto

```
Translate_v1/
├── translate_speech_env/
│   ├── translate_gui.py           # Interfaz gráfica
│   ├── translate_realtime.py      # Lógica principal + CLI
│   ├── record_audio.py            # Utilidad para grabar audio
│   ├── test_tts.py                # Test de TTS
│   ├── list_voices.py             # Listar voces disponibles
│   ├── requirements.txt           # Dependencias
│   ├── run_gui.bat                # Inicio rápido GUI
│   ├── README_GUI.md              # Guía de la GUI
│   ├── PUSH_TO_TALK.md            # Guía Push-to-Talk
│   ├── OPTIMIZACIONES.md          # Detalles de optimizaciones
│   ├── MEJORAS_VELOCIDAD.md       # Historial de mejoras
│   └── MEJORAS_AUDIO.md           # Mejoras de calidad de audio (NEW ⭐)
├── .gitignore
└── README.md                      # Este archivo
```

---

## 🎯 Casos de Uso

### 📚 Aprender Inglés
- Practica pronunciación
- Escucha traducciones correctas
- Modo Continuo recomendado

### 🎮 Gaming
- Traduce chat de voz
- Modo Push-to-Talk
- Modelo Rápido

### 📞 Llamadas
- Traduce conversaciones
- Modo Push-to-Talk
- Modelo Balanced

### 🎥 Videos/Películas
- Traduce diálogos
- Modo Continuo
- Modelo Preciso

---

## ⚙️ Configuración Avanzada

### Cambiar Velocidad de Voz
En `translate_realtime.py` o `translate_gui.py`:
```python
engine.setProperty('rate', 185)  # 150-200 recomendado
```

### Usar GPU (NVIDIA)
```python
model = whisper.load_model("base", device="cuda")
```
**Mejora:** 10-20x más rápido

### Ajustar Duración de Chunks
En `translate_realtime.py`:
```python
self.chunk_duration = 3  # 2-5 segundos
```

---

## 🐛 Solución de Problemas

### "No se encuentra módulo whisper"
```bash
pip install openai-whisper
```

### "Error de COM en TTS"
- Asegúrate de estar en Windows
- Reinstala: `pip install --upgrade pywin32`

### "No detecta la barra espaciadora"
- Ejecuta como administrador
- Verifica que la ventana tenga foco

### "Audio muy lento"
- Usa modelo "Rápido" (Tiny)
- Reduce chunk_duration a 2
- Considera usar GPU

---

## 📊 Rendimiento

### Latencia por Modo

| Configuración | Latencia |
|---------------|----------|
| PTT + Rápido | 0.7-1.6s ⚡⚡⚡ |
| PTT + Balanced | 1.2-2.3s ⚡⚡ |
| PTT + Preciso | 2.2-3.5s ⚡ |
| Continuo + Rápido | 3.7-4.6s |
| Continuo + Balanced | 4.2-5.3s |

### Con GPU NVIDIA

| Configuración | Latencia |
|---------------|----------|
| PTT + Rápido + GPU | 0.25-0.5s ⚡⚡⚡⚡ |
| PTT + Balanced + GPU | 0.45-0.9s ⚡⚡⚡ |

---

## 🛠️ Desarrollo

### Ejecutar Tests
```bash
# Test de TTS
python translate_speech_env/test_tts.py

# Listar voces disponibles
python translate_speech_env/list_voices.py

# Grabar audio de prueba
python translate_speech_env/record_audio.py
```

### Contribuir
1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Roadmap

- [ ] Soporte para más idiomas
- [ ] Detección automática de idioma
- [ ] Exportar traducciones a archivo
- [ ] Modo bidireccional (ES↔EN)
- [ ] Interfaz web
- [ ] App móvil (Android/iOS)
- [ ] Tema oscuro en GUI
- [ ] Historial de sesiones

---

## 🤝 Créditos

### Tecnologías Utilizadas
- [OpenAI Whisper](https://github.com/openai/whisper) - Transcripción
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Text-to-Speech
- [sounddevice](https://python-sounddevice.readthedocs.io/) - Captura de audio
- [keyboard](https://github.com/boppreh/keyboard) - Detección de teclas

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👤 Autor

**Marlon**

- GitHub: [@MarlonESuarez](https://github.com/MarlonESuarez)

---

## ⭐ Agradecimientos

- OpenAI por Whisper
- Comunidad de Python
- Todos los contribuidores

---

## 📬 Contacto

Si tienes preguntas o sugerencias:
- Abre un [Issue](https://github.com/MarlonESuarez/Translate_in_real_time/issues)
- Contacta: mwolfvix@gmail.com

---

**¡Disfruta traduciendo! 🎤🌍**
