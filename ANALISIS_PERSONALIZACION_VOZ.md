# 🎙️ Análisis: Personalización y Adaptación a la Voz del Usuario

## 📋 Requisito del Usuario

> "Entrenar el modelo para que se adapte a la voz del usuario, teniendo en cuenta acentos y maneras de hablar. Proceso de calibración donde el usuario lee un texto, el modelo analiza su voz y se adapta."

---

## 🔍 Investigación Realizada

### 1. **Fine-tuning de Whisper (Adaptación completa del modelo)**

#### **LoRA (Low-Rank Adaptation)** ⭐ Más prometedor
- **Qué es:** Congela pesos originales y entrena solo matrices pequeñas de bajo rango
- **Ventajas:**
  - Solo 1% de parámetros entrenables (~60MB vs 6GB)
  - Funciona con 8GB GPU (vs 40GB+ para full fine-tuning)
  - 5x más rápido que fine-tuning completo
  - Checkpoints muy pequeños (fácil distribución)
- **Tiempo:** 6-8 horas con dataset de 12 horas (Common Voice)
- **Repositorio principal:** [Vaibhavs10/fast-whisper-finetuning](https://github.com/Vaibhavs10/fast-whisper-finetuning)
- **Librerías:** `peft`, `bitsandbytes`, `accelerate`, `transformers`

#### **Prompt Tuning para Target-Speaker ASR**
- **Qué es:** Usa embeddings del speaker + prompts entrenables
- **Ventajas:**
  - Solo 1% de parámetros del modelo
  - Rendimiento comparable a full training
  - Mitiga overfitting con datos limitados
- **Paper:** [Extending Whisper with Prompt Tuning](https://arxiv.org/html/2312.08079v2)

---

### 2. **Speaker Adaptation (Adaptación sin re-entrenar Whisper)**

#### **Speaker Embeddings (i-vectors / x-vectors)**
- **Qué son:** Vectores de baja dimensión que capturan características únicas del speaker
- **Ventajas:**
  - No requiere re-entrenar Whisper
  - Extracción rápida (milisegundos)
  - Se pueden usar para filtrado/ponderación
- **Librerías:**
  - `pyannote.audio` - x-vectors con arquitectura TDNN
  - `speechbrain` - Modelos pre-entrenados en VoxCeleb
- **Uso típico:** Speaker diarization, verificación, clustering

#### **GLoRA (Generalized Low-Rank Adaptation)**
- **Qué es:** Fine-tuning eficiente específico por speaker
- **Ventajas:**
  - 20% mejora en WER con datos muy limitados
  - Eficiente en parámetros y cómputo
- **Fuente:** [Samsung Research](https://research.samsung.com/blog/Robust-Speaker-Personalisation-Using-Generalized-Low-Rank-Adaptation-for-Automatic-Speech-Recognition)

---

### 3. **Voice Enrollment / Calibration (Proceso de calibración)**

#### **Proceso tradicional (Dragon, Windows Speech Recognition):**
1. Usuario lee texto predefinido (15-60 minutos)
2. Sistema crea perfil de voz
3. Aprende de correcciones en uso continuo
4. **Mejora:** Dramática en precisión con solo 15 min

#### **Factores críticos:**
- **Hardware:** Micrófono de alta calidad (headset preferido)
- **Ambiente:** Silencioso, consistente
- **Datos:** Diversidad de fonemas, palabras comunes del usuario
- **Longitud:** 15-60 min lectura = mejora significativa

---

## 🎯 **SOLUCIONES PROPUESTAS** (3 Niveles de Complejidad)

---

### **NIVEL 1: RÁPIDO Y SIMPLE** ⚡ (Recomendado para empezar)

#### **Voice Enrollment Básico + Audio Profiling**

**Qué hace:**
1. Usuario lee 5-10 frases en español (2-3 minutos)
2. Sistema analiza y guarda:
   - Nivel promedio de volumen (RMS personalizado)
   - Frecuencia fundamental (pitch)
   - Rango dinámico
   - Patrón de energía
3. Ajusta preprocesamiento en tiempo real:
   - RMS normalization personalizada
   - VAD threshold adaptativo
   - Filtrado de frecuencias personalizado

**Ventajas:**
- ✅ **Fácil implementación** (2-3 días desarrollo)
- ✅ **Sin GPU requerida**
- ✅ **Sin re-entrenar Whisper**
- ✅ **Mejora inmediata en robustez**
- ✅ **Compatible con sistema actual**

**Desventajas:**
- ❌ No adapta el modelo Whisper en sí
- ❌ Mejora limitada (~5-10%)

**Implementación:**
```python
# Pseudocódigo
class VoiceProfile:
    def __init__(self):
        self.target_rms = -20  # Default
        self.pitch_range = (80, 300)  # Default
        self.vad_threshold = 0.5  # Default

    def calibrate(self, audio_samples):
        """Analiza voz del usuario y ajusta parámetros"""
        # Calcular RMS promedio del usuario
        self.target_rms = calculate_user_rms(audio_samples)

        # Detectar pitch range
        self.pitch_range = extract_pitch_range(audio_samples)

        # Ajustar VAD threshold según energía típica
        self.vad_threshold = adaptive_vad_threshold(audio_samples)

    def apply(self, audio_chunk):
        """Aplica perfil personalizado a audio en tiempo real"""
        audio_chunk = normalize_to_user_rms(audio_chunk, self.target_rms)
        return audio_chunk
```

**Tiempo:** 2-3 días implementación

---

### **NIVEL 2: INTERMEDIO** ⚙️ (Mejor relación esfuerzo/resultado)

#### **Speaker Embeddings + Whisper Personalizado**

**Qué hace:**
1. Usuario lee 10 frases (5 min)
2. Extrae speaker embedding (x-vector) con `speechbrain`
3. Guarda embedding como "firma de voz"
4. En tiempo real:
   - Compara audio entrante con embedding guardado
   - Ajusta confianza de VAD según similitud
   - Filtra mejor ruido vs. voz del usuario
5. **Opcional:** Crea dataset personalizado con las grabaciones

**Ventajas:**
- ✅ **Mejora significativa** (~10-20%)
- ✅ **Sin re-entrenar Whisper** (inicialmente)
- ✅ **Embeddings pequeños** (<1KB)
- ✅ **Multi-usuario** (varios perfiles)
- ✅ **Base para fine-tuning futuro**

**Desventajas:**
- ❌ Requiere instalar `speechbrain` (~500MB)
- ❌ Más complejo (1 semana desarrollo)

**Implementación:**
```python
from speechbrain.pretrained import EncoderClassifier

class SpeakerAdaptation:
    def __init__(self):
        # Cargar modelo pre-entrenado de x-vectors
        self.encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-xvect-voxceleb"
        )
        self.user_embedding = None

    def enroll_user(self, audio_samples):
        """Crea perfil de voz del usuario"""
        self.user_embedding = self.encoder.encode_batch(audio_samples)

    def verify_speaker(self, audio_chunk):
        """Verifica si audio pertenece al usuario"""
        chunk_embedding = self.encoder.encode_batch(audio_chunk)
        similarity = cosine_similarity(self.user_embedding, chunk_embedding)
        return similarity > 0.75  # Threshold
```

**Tiempo:** 5-7 días implementación

---

### **NIVEL 3: AVANZADO** 🚀 (Máxima precisión)

#### **LoRA Fine-tuning de Whisper**

**Qué hace:**
1. Proceso de calibración extendido:
   - Usuario lee 50-100 frases (20-30 min)
   - Frases cubren diversos fonemas del español
   - Sistema graba + guarda con transcripciones
2. Fine-tuning con LoRA:
   - Entrena modelo Whisper en voz del usuario
   - Solo 60MB de pesos adicionales
   - Preserva capacidad general del modelo
3. Carga modelo personalizado en producción

**Ventajas:**
- ✅ **Máxima precisión** (+20-40% mejora)
- ✅ **Específico para acento del usuario**
- ✅ **Modelo compacto** (60MB vs 6GB)
- ✅ **Preserva conocimiento general**

**Desventajas:**
- ❌ **Requiere GPU** (8GB+ VRAM)
- ❌ **Tiempo de entrenamiento** (2-4 horas por usuario)
- ❌ **Complejidad alta** (2-3 semanas desarrollo)
- ❌ **Proceso offline** (no en tiempo real)

**Arquitectura:**
```
Usuario → Calibración (30 min lectura)
    ↓
Grabación + Transcripciones guardadas
    ↓
Fine-tuning LoRA offline (2-4 horas GPU)
    ↓
Modelo personalizado (60MB)
    ↓
Carga en producción → Traducción mejorada
```

**Implementación:**
```python
# Usando Hugging Face PEFT
from peft import LoraConfig, get_peft_model

# Configurar LoRA
lora_config = LoraConfig(
    r=8,  # Rank bajo
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],  # Capas de atención
    lora_dropout=0.05,
    bias="none"
)

# Aplicar LoRA a Whisper
model = get_peft_model(whisper_model, lora_config)

# Fine-tuning con datos del usuario (offline)
trainer.train()

# Guardar solo pesos LoRA (~60MB)
model.save_pretrained("whisper_user_profile_marlon")
```

**Tiempo:** 2-3 semanas implementación completa

---

## 📊 **COMPARACIÓN DE SOLUCIONES**

| Característica | Nivel 1: Básico | Nivel 2: Embeddings | Nivel 3: LoRA |
|----------------|-----------------|---------------------|---------------|
| **Mejora precisión** | +5-10% | +10-20% | +20-40% |
| **Tiempo calibración** | 2-3 min | 5 min | 20-30 min |
| **Requiere GPU** | ❌ No | ❌ No | ✅ Sí (8GB+) |
| **Tiempo desarrollo** | 2-3 días | 5-7 días | 2-3 semanas |
| **Complejidad** | Baja | Media | Alta |
| **Multi-usuario** | ✅ Sí | ✅ Sí | ✅ Sí (1 modelo/usuario) |
| **Tamaño perfil** | <1KB | <1KB | ~60MB |
| **Tiempo procesamiento** | 0ms | +5-10ms | 0ms (offline) |
| **Compatible ahora** | ✅ 100% | ✅ 90% | ⚠️ Requiere refactor |

---

## 🎯 **RECOMENDACIÓN: ENFOQUE HÍBRIDO (Fases)**

### **FASE 1 (Inmediato): Voice Profiling Básico**
- Implementar Nivel 1 (2-3 días)
- Calibración rápida (2-3 min)
- Mejora modesta pero inmediata (+5-10%)
- **Sin riesgo, fácil rollback**

### **FASE 2 (1-2 semanas): Speaker Embeddings**
- Implementar Nivel 2 (5-7 días)
- Recolectar datos de usuarios reales
- Mejora significativa (+10-20%)
- **Base para Fase 3**

### **FASE 3 (Futuro, 2-3 meses): LoRA Fine-tuning**
- Solo si FASE 2 demuestra necesidad
- Requerir GPU cloud (AWS/GCP)
- Proceso automatizado de fine-tuning
- **Máxima precisión (+20-40%)**

---

## 🛠️ **PROCESO DE CALIBRACIÓN PROPUESTO (Nivel 1 + 2)**

### **Flujo de Usuario:**

```
1. Primera vez (5 minutos):
   ┌─────────────────────────────────────┐
   │ "Calibrar Voz" (nuevo botón en GUI) │
   └─────────────────────────────────────┘
                    ↓
   ┌─────────────────────────────────────┐
   │ Instrucciones en pantalla:          │
   │ "Lee las siguientes 10 frases       │
   │  en voz alta para calibrar"         │
   └─────────────────────────────────────┘
                    ↓
   ┌─────────────────────────────────────┐
   │ Frase 1/10:                         │
   │ "Hola, mi nombre es [nombre]"       │
   │                                     │
   │ [🎤 Mantén ESPACIO para grabar]     │
   │                                     │
   │ ━━━━━━━━━━━━━━━ 40%                │
   └─────────────────────────────────────┘
                    ↓
   (Repite para 10 frases)
                    ↓
   ┌─────────────────────────────────────┐
   │ "Analizando tu voz..."              │
   │ ⏳ Procesando...                     │
   └─────────────────────────────────────┘
                    ↓
   ┌─────────────────────────────────────┐
   │ ✅ "Perfil de voz creado!"           │
   │                                     │
   │ Tu nombre: Marlon                   │
   │ Calidad de muestra: Excelente       │
   │                                     │
   │ [Continuar]                         │
   └─────────────────────────────────────┘

2. Uso normal:
   - Sistema carga perfil automáticamente
   - Aplica ajustes personalizados
   - Usuario nota mejor precisión
```

### **10 Frases Calibración (Español):**

1. "Hola, mi nombre es [nombre del usuario]"
2. "Me gusta practicar inglés todos los días"
3. "¿Qué hora es? Son las tres de la tarde"
4. "El clima está muy agradable hoy"
5. "Necesito comprar pan y leche en el supermercado"
6. "Mi trabajo es muy interesante y desafiante"
7. "Los números importantes son: cero, uno, cinco, diez, veinte"
8. "Me encanta escuchar música mientras trabajo"
9. "Voy a viajar a la playa este fin de semana"
10. "Gracias por tu ayuda, hasta luego"

**Razón de estas frases:**
- ✅ Cubren vocales: a, e, i, o, u
- ✅ Consonantes comunes: r, l, s, n, d, t
- ✅ Números (útiles para traducción)
- ✅ Palabras frecuentes en conversación
- ✅ Diferentes estructuras gramaticales

---

## 💾 **ESTRUCTURA DE DATOS DEL PERFIL**

```python
# voice_profile.json
{
    "user_name": "Marlon",
    "created_at": "2025-10-21T10:30:00",
    "version": "1.0",

    # Audio characteristics
    "audio_profile": {
        "target_rms_db": -18.5,      # RMS personalizado
        "pitch_range": [95, 280],     # Hz (F0 range)
        "speaking_rate": 4.2,         # sílabas/segundo
        "dynamic_range": 15.3         # dB
    },

    # VAD personalization
    "vad_config": {
        "threshold": 0.42,            # Ajustado a su voz
        "min_speech_duration": 0.4    # Ajustado a su patrón
    },

    # Speaker embedding (Nivel 2)
    "speaker_embedding": {
        "model": "speechbrain/xvector-voxceleb",
        "vector": [0.234, -0.112, ...],  # 512 dimensiones
        "similarity_threshold": 0.75
    },

    # Calibration metadata
    "calibration_audio": [
        {
            "phrase_id": 1,
            "text": "Hola, mi nombre es Marlon",
            "duration": 2.3,
            "quality_score": 0.95,
            "file_path": "profiles/marlon/phrase_1.wav"
        },
        # ... 9 más
    ],

    # Statistics
    "usage_stats": {
        "sessions": 15,
        "total_translations": 234,
        "average_confidence": 0.87,
        "last_used": "2025-10-21T14:20:00"
    }
}
```

---

## 🔄 **INTEGRACIÓN CON CÓDIGO ACTUAL**

### **Cambios mínimos necesarios (Nivel 1):**

```python
# translate_realtime.py

class RealtimeTranslator:
    def __init__(self, ..., voice_profile=None):
        # ... código existente ...

        # NUEVO: Voice profiling
        self.voice_profile = voice_profile or VoiceProfile()

        # Si hay perfil, usar parámetros personalizados
        if voice_profile:
            self.target_rms_db = voice_profile.target_rms_db
            self.vad_threshold = voice_profile.vad_threshold

    def process_audio_worker(self):
        # ... código existente ...

        # MODIFICADO: Aplicar perfil antes de Whisper
        if self.voice_profile:
            audio_prepared = self.voice_profile.apply(audio_prepared)

        # Continúa con Whisper...
```

**Impacto:** Mínimo (1-2 días integración)

---

## 📈 **ROADMAP PROPUESTO**

```
Semana 1-2: FASE 1 - Voice Profiling Básico
├── Diseño UI de calibración
├── Implementar análisis de audio
├── Guardar/cargar perfiles
├── Integrar con traductor
└── Testing con 5-10 usuarios

Semana 3-4: FASE 2 - Speaker Embeddings
├── Integrar SpeechBrain
├── Extracción de x-vectors
├── Sistema multi-usuario
├── Mejoras de VAD personalizado
└── Testing extensivo

Mes 3-4: FASE 3 (Opcional) - LoRA Fine-tuning
├── Setup infraestructura GPU
├── Pipeline de fine-tuning automatizado
├── Interfaz para entrenar modelos
├── Validación de modelos personalizados
└── Deployment de modelos

```

---

## ✅ **PRÓXIMO PASO SUGERIDO**

**IMPLEMENTAR FASE 1 (Voice Profiling Básico):**

1. ✅ Crear interfaz de calibración en GUI
2. ✅ Implementar análisis de audio (RMS, pitch, etc.)
3. ✅ Sistema de perfiles (guardar/cargar JSON)
4. ✅ Integrar con flujo actual
5. ✅ Testing con tu voz

**Estimado:** 2-3 días desarrollo + 1-2 días testing

¿Quieres que empecemos con la **Fase 1** ahora mismo?

