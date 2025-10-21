# Traductor de Voz - Interfaz Gráfica

## 🎨 Interfaz Gráfica Amigable

Aplicación de escritorio con interfaz limpia y moderna para traducir voz de español a inglés en tiempo real.

---

## 🚀 Inicio Rápido

### Método 1: Doble clic
```
Hacer doble clic en: run_gui.bat
```

### Método 2: PowerShell
```powershell
.\Scripts\python.exe translate_gui.py
```

---

## 📱 Características de la Interfaz

### ✅ Sin Interacción con Terminal
- Todo funciona desde la ventana gráfica
- No requiere comandos
- No hay prompts de terminal

### ✅ Diseño Limpio
- Fondo blanco sólido (sin gradientes)
- Colores planos modernos
- Layout organizado
- Fuentes claras

### ✅ Controles Visuales
- Radio buttons para configuración
- Botones grandes y claros
- Indicadores de estado con colores
- Área de texto con scroll

---

## 🎯 Cómo Usar

### 1. Configurar

**Modo de Grabación:**
- ○ **Continuo**: Graba automáticamente todo el tiempo
- ○ **Push-to-Talk**: Solo graba al presionar ESPACIO

**Calidad:**
- ○ **Rápido**: Más veloz (modelo Tiny)
- ● **Balanced**: Balance ideal (modelo Base) ⭐
- ○ **Preciso**: Mejor calidad (modelo Small)

### 2. Iniciar

Clic en **[▶ Iniciar]**

El estado cambiará a:
- **● Grabando...** (verde) en modo Continuo
- **● Esperando ESPACIO...** (naranja) en modo Push-to-Talk

### 3. Hablar

**Modo Continuo:**
- Habla normalmente en español
- El sistema procesa cada 3 segundos

**Modo Push-to-Talk:**
- Presiona y MANTÉN la barra ESPACIO
- Habla en español
- Suelta ESPACIO cuando termines
- Estado cambia a **● Procesando...** (azul)

### 4. Ver Traducciones

Las traducciones aparecen en el área de texto:
```
→ Hello, how are you?
→ My name is Jorge
→ What time is it?
```

### 5. Detener

Clic en **[■ Detener]**

---

## 🎨 Elementos Visuales

### Estados con Colores

| Estado | Color | Significado |
|--------|-------|-------------|
| ● Detenido | Gris | App no está grabando |
| ● Grabando... | Verde | Capturando audio |
| ● Esperando ESPACIO... | Naranja | Modo PTT activo |
| ● Procesando... | Azul | Traduciendo audio |

### Área de Traducciones

- **Verde**: Traducciones al inglés
- **Gris**: Mensajes de estado
- **Scroll**: Ver traducciones anteriores

### Footer

- **Contador**: "Traducciones: 5"

---

## ⌨️ Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| **ESPACIO** | Grabar (solo en modo Push-to-Talk) |
| *Ninguno más* | Todo se hace con clicks |

---

## 📊 Ventajas vs Terminal

| Aspecto | Terminal | GUI |
|---------|----------|-----|
| **Facilidad** | Media | Alta ✅ |
| **Visual** | Texto | Colores e iconos ✅ |
| **Configuración** | Escribir números | Radio buttons ✅ |
| **Estado** | Texto | Indicador con color ✅ |
| **Historial** | No | Scroll de traducciones ✅ |
| **Estadísticas** | Al final | Tiempo real ✅ |

---

## 🐛 Solución de Problemas

### "No inicia al hacer doble clic en run_gui.bat"
- Abre PowerShell en la carpeta
- Ejecuta: `.\Scripts\python.exe translate_gui.py`
- Lee el mensaje de error

### "Modo Push-to-Talk no responde"
- Asegúrate de que la ventana de la GUI tenga foco
- Presiona ESPACIO dentro de la ventana
- Verifica que el estado cambie a "Grabando..."

### "No aparecen traducciones"
- Verifica que el micrófono esté funcionando
- Habla más fuerte
- Intenta con modelo "Rápido" primero
- Mira el área de texto por mensajes de error

### "Error al iniciar"
- Verifica que las dependencias estén instaladas
- Ejecuta: `pip install -r requirements.txt`
- Reinicia la aplicación

---

## 📂 Archivos de la GUI

```
translate_speech_env/
├── translate_gui.py        ← Aplicación con GUI
├── translate_realtime.py   ← Lógica del traductor
├── run_gui.bat            ← Inicio rápido
└── README_GUI.md          ← Esta guía
```

---

## 🎯 Casos de Uso

### 📚 Estudiar Inglés
1. Modo: Continuo
2. Calidad: Preciso
3. Habla frases en español y escucha la traducción

### 🎮 Gaming
1. Modo: Push-to-Talk
2. Calidad: Rápido
3. Presiona ESPACIO para traducir chat

### 📞 Llamadas
1. Modo: Push-to-Talk
2. Calidad: Balanced
3. Traduce frases específicas

### 🎥 Ver Videos
1. Modo: Continuo
2. Calidad: Balanced
3. Traduce diálogos automáticamente

---

## 🔄 Actualizaciones Futuras

Posibles mejoras:
- [ ] Selector de idiomas (no solo ES→EN)
- [ ] Botón para limpiar traducciones
- [ ] Exportar traducciones a archivo
- [ ] Tema oscuro
- [ ] Personalizar tecla PTT
- [ ] Atajos de teclado globales
- [ ] Minimizar a bandeja del sistema

---

## 📝 Notas Técnicas

### Tecnologías
- **GUI**: Tkinter (incluido con Python)
- **Voz**: Whisper (OpenAI)
- **TTS**: pyttsx3
- **Audio**: sounddevice

### Requisitos
- Windows 10/11
- Python 3.11+
- Micrófono
- Altavoces/Audífonos

---

¡Disfruta de la interfaz gráfica! 🎨

Si encuentras algún problema, revisa la sección de Solución de Problemas o ejecuta desde PowerShell para ver mensajes de error.
