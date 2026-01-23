# Question Generator v2

Generador de preguntas para estudio desde documentos PDF legales usando LLMs.

## Características

- **Múltiples proveedores de LLM**: Kimi, Groq, OpenAI, Ollama (local)
- **4 tipos de preguntas**: Flashcards, Verdadero/Falso, Opción Múltiple, Cloze
- **Pipeline automatizado**: Extracción → Clasificación → Generación → Validación
- **Clasificación semántica**: 4 métricas para filtrar contenido relevante
- **Arquitectura limpia**: Fácil de extender y mantener
- **Tracking de experimentos**: Reproducibilidad y análisis de costos

## Instalación

```bash
cd v2-question-generator
pip install -e .
```

## Configuración

### 1. Variables de entorno

```bash
# Elige uno o más proveedores
export MOONSHOT_API_KEY=tu_api_key_de_kimi
export GROQ_API_KEY=tu_api_key_de_groq
export OPENAI_API_KEY=tu_api_key_de_openai
```

### 2. Crear archivo de configuración

```bash
qgen config init
```

## Uso

### Pipeline completo

```bash
# Genera flashcards desde un PDF
qgen pipeline documento.pdf --type flashcard

# Usa Groq en lugar de Kimi
qgen pipeline documento.pdf --type multiple_choice --provider groq

# Omite etapas si ya fueron ejecutadas
qgen pipeline documento.pdf --skip extract classify
```

### Comandos individuales

```bash
# Extraer secciones
qgen extract documento.pdf

# Clasificar secciones
qgen classify DOC_ID --threshold 0.7

# Generar preguntas
qgen generate DOC_ID --type true_false --provider kimi

# Validar preguntas
qgen validate DOC_ID --level strict --fix
```

### Gestión de configuración

```bash
# Ver configuración actual
qgen config show

# Ver proveedores configurados
qgen config providers
```

## Tipos de Preguntas

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `flashcard` | Pregunta y respuesta | "¿Qué es X?" → "X es..." |
| `true_false` | Afirmación V/F con justificación | "El artículo 1 establece..." → Verdadero |
| `multiple_choice` | 4 opciones con una correcta | "¿Cuál es...?" A) B) C) D) |
| `cloze` | Texto con espacios a completar | "El {{c1::plazo}} es de 30 días" |

## Proveedores de LLM

| Proveedor | Ventajas | Mejor para |
|-----------|----------|------------|
| **Kimi** | Contexto 128k, económico | Documentos largos |
| **Groq** | Ultra-rápido | Procesamiento batch |
| **OpenAI** | Alta calidad | Preguntas complejas |
| **Ollama** | Gratis, local | Desarrollo y testing |

## Estructura del Proyecto

```
v2-question-generator/
├── src/
│   ├── domain/          # Entidades y value objects
│   ├── application/     # Casos de uso y puertos
│   ├── infrastructure/  # Implementaciones (LLM, PDF, DB)
│   └── interface/       # CLI
├── prompts/             # Prompts por tipo de pregunta
├── config/              # Archivos de configuración
├── tests/               # Tests unitarios e integración
└── docs/                # Documentación
```

## Salidas

El pipeline genera:

1. **CSV de secciones**: `datos/intermediate/secciones_*.csv`
2. **JSON de preguntas**: `datos/procesadas/preguntas_*.json`
3. **Experimentos**: `datos/experiments/experiments.json`

## Documentación

- [Arquitectura](docs/ARCHITECTURE.md): Diseño y patrones
- [Análisis v1](ANALISIS_SITUACION_ACTUAL.md): Problemas y soluciones

## Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Formatear código
black src tests
isort src tests

# Type checking
mypy src
```

## Licencia

MIT
