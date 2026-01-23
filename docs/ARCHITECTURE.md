# Arquitectura Question Generator v2

## Visión General

Question Generator v2 implementa una **Arquitectura Hexagonal (Clean Architecture)** que separa claramente las responsabilidades y permite:

- **Testabilidad**: Cada capa puede probarse de forma aislada
- **Flexibilidad**: Cambiar proveedores de LLM sin modificar lógica de negocio
- **Mantenibilidad**: Código organizado por responsabilidades
- **Extensibilidad**: Añadir nuevos tipos de preguntas o backends fácilmente

## Capas de la Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     INTERFACE LAYER                         │
│                        (CLI)                                │
├─────────────────────────────────────────────────────────────┤
│                   APPLICATION LAYER                         │
│              (Use Cases + Ports)                            │
├─────────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                            │
│           (Entities + Value Objects)                        │
├─────────────────────────────────────────────────────────────┤
│                 INFRASTRUCTURE LAYER                        │
│        (LLM Backends, PDF, Persistence, Config)             │
└─────────────────────────────────────────────────────────────┘
```

### 1. Domain Layer (`src/domain/`)

Contiene la lógica de negocio pura sin dependencias externas.

**Entidades:**
- `Document`: Representa un PDF con su hash para evitar reprocesamiento
- `Section`: Sección extraída del PDF con coordenadas y clasificación
- `Question`: Pregunta generada con soporte para múltiples tipos
- `Batch`: Grupo de secciones para procesamiento por LLM

**Value Objects:**
- `Coordinates`: Posición y dimensiones en el PDF
- `ClassificationResult`: Resultado de clasificación semántica (4 métricas)
- `Origin`: Trazabilidad a sección de origen
- `QuestionMetadata`: Metadatos SM-2 para repetición espaciada

### 2. Application Layer (`src/application/`)

Orquesta la lógica de negocio a través de casos de uso.

**Puertos (Interfaces):**
- `LLMService`: Contrato para cualquier backend de LLM
- `PDFExtractorService`: Contrato para extracción de PDF
- `ClassificationService`: Contrato para clasificación semántica
- `PromptService`: Contrato para gestión de prompts
- Repositorios: `SectionRepository`, `QuestionRepository`, `DocumentRepository`

**Casos de Uso:**
- `ExtractSectionsUseCase`: Etapa 1 - Extracción del PDF
- `ClassifySectionsUseCase`: Etapa 2 - Clasificación semántica
- `GenerateQuestionsUseCase`: Etapa 3 - Generación con LLM
- `ValidateQuestionsUseCase`: Etapa 4 - Validación de preguntas
- `RunPipelineUseCase`: Orquestación del pipeline completo

### 3. Infrastructure Layer (`src/infrastructure/`)

Implementaciones concretas de los puertos.

**LLM Backends:**
- `KimiBackend`: Moonshot AI (contexto 128k)
- `GroqBackend`: Inferencia ultra-rápida
- `OpenAIBackend`: GPT-4, GPT-4o
- `OllamaBackend`: Modelos locales

**Otros Adaptadores:**
- `SpacyLayoutExtractor`: Extracción de PDF con spacy-layout
- `SectionRepositoryCSV`: Persistencia en CSV
- `QuestionRepositoryJSON`: Persistencia en JSON
- `PromptServiceImpl`: Gestión de prompts versionados
- `ConfigLoader`: Carga de configuración desde múltiples fuentes

### 4. Interface Layer (`src/interface/`)

Puntos de entrada a la aplicación.

**CLI:**
- `qgen extract`: Extrae secciones de PDF
- `qgen classify`: Clasifica secciones
- `qgen generate`: Genera preguntas
- `qgen validate`: Valida preguntas
- `qgen pipeline`: Ejecuta pipeline completo
- `qgen config`: Gestiona configuración

## Flujo de Datos

```
PDF → Extract → Sections → Classify → Relevant Sections → Generate → Questions → Validate → Output
      (Etapa 1)           (Etapa 2)                       (Etapa 3)            (Etapa 4)
```

### Etapa 1: Extracción
1. PDF es procesado por `SpacyLayoutExtractor`
2. Se extraen secciones con título, texto, página y coordenadas
3. Se crea `Document` con hash para caché
4. Secciones se guardan en CSV

### Etapa 2: Clasificación
1. Cada sección se evalúa con 4 métricas:
   - AS (30%): Aptitud Semántica
   - RJ (40%): Relevancia Jurídica
   - DC (20%): Densidad Conceptual
   - CC (10%): Claridad Contextual
2. Se asigna clasificación: RELEVANT, REVIEW_NEEDED, AUTO_CONSERVED, DISCARDABLE

### Etapa 3: Generación
1. Secciones relevantes se agrupan en batches
2. Se construye prompt con `PromptService`
3. Se envía a LLM seleccionado
4. Se parsea respuesta JSON
5. Se crean objetos `Question`

### Etapa 4: Validación
1. Cada pregunta se valida según reglas por tipo
2. Se detectan problemas (longitud, formato, contenido)
3. Opcionalmente se aplican correcciones automáticas
4. Se marca status: VALIDATED o INVALID

## Patrones de Diseño

### Strategy + Factory (LLM Backends)

```python
# Factory crea backend según proveedor
backend = LLMFactory.create(LLMProvider.KIMI, config)

# Todos implementan la misma interfaz
response = backend.generate(prompt, system_prompt)
```

### Repository Pattern

```python
# Abstracción de persistencia
sections = section_repository.find_relevant(document_id)
question_repository.save_all(questions)
```

### Dependency Injection

```python
# Use cases reciben dependencias por constructor
use_case = GenerateQuestionsUseCase(
    llm_service=llm_service,          # Interfaz
    prompt_service=prompt_service,     # Interfaz
    section_repository=section_repo,   # Interfaz
    ...
)
```

### Template Method (BaseLLMBackend)

```python
# Clase base implementa flujo común
# Subclases implementan detalles específicos
class BaseLLMBackend:
    def generate(self, prompt, ...):
        # 1. Cache lookup
        # 2. _call_api() - abstracto
        # 3. Cache store
        # 4. Parse response
```

## Tipos de Preguntas

| Tipo | Descripción | Campos Específicos |
|------|-------------|-------------------|
| `flashcard` | Pregunta-respuesta | `front`, `back` |
| `true_false` | Verdadero/Falso | `statement`, `answer`, `justification` |
| `multiple_choice` | Opción múltiple | `options`, `correct_index`, `justification` |
| `cloze` | Completar espacios | `text_with_blanks`, `valid_answers` |

## Configuración

### Variables de Entorno

```bash
MOONSHOT_API_KEY=xxx    # Para Kimi
GROQ_API_KEY=xxx        # Para Groq
OPENAI_API_KEY=xxx      # Para OpenAI
OLLAMA_HOST=xxx         # Para Ollama remoto
```

### Archivo config.json

```json
{
  "default_llm_provider": "kimi",
  "llm": {
    "kimi": {"model": "moonshot-v1-128k"},
    "groq": {"model": "llama-3.3-70b-versatile"}
  },
  "classification": {
    "threshold_relevant": 0.7,
    "threshold_review": 0.5
  },
  "generation": {
    "default_batch_size": 5,
    "default_question_type": "flashcard"
  }
}
```

## Estructura de Directorios

```
v2-question-generator/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── document.py
│   │   │   ├── section.py
│   │   │   ├── question.py
│   │   │   └── batch.py
│   │   └── value_objects/
│   │       ├── coordinates.py
│   │       ├── classification.py
│   │       ├── origin.py
│   │       └── metadata.py
│   ├── application/
│   │   ├── ports/
│   │   │   ├── repositories/
│   │   │   └── services/
│   │   └── use_cases/
│   │       ├── extract_sections.py
│   │       ├── classify_sections.py
│   │       ├── generate_questions.py
│   │       ├── validate_questions.py
│   │       └── run_pipeline.py
│   ├── infrastructure/
│   │   ├── llm/
│   │   │   ├── backends/
│   │   │   ├── prompt_manager/
│   │   │   └── factory.py
│   │   ├── pdf/
│   │   ├── persistence/
│   │   │   ├── csv/
│   │   │   └── json/
│   │   └── config/
│   └── interface/
│       └── cli/
│           └── commands/
├── tests/
├── prompts/
├── config/
└── docs/
```

## Extensibilidad

### Añadir Nuevo Proveedor de LLM

1. Crear clase en `infrastructure/llm/backends/`
2. Extender `BaseLLMBackend`
3. Implementar métodos abstractos
4. Registrar en `LLMFactory`

### Añadir Nuevo Tipo de Pregunta

1. Añadir valor a `QuestionType` enum
2. Crear dataclass de contenido en `question.py`
3. Añadir factory method `create_xxx()`
4. Crear prompt en `prompts/xxx/`
5. Actualizar validaciones en `ValidateQuestionsUseCase`

### Añadir Nuevo Formato de Exportación

1. Añadir método en `QuestionRepositoryJSON`
2. Actualizar `export_to_json()` con nuevo formato

## Migración desde v1

La arquitectura v2 mantiene compatibilidad con:
- Formato CSV de secciones
- Formato JSON de preguntas
- Estructura de prompts

Pasos para migrar:
1. Copiar prompts a `prompts/` manteniendo estructura
2. Importar secciones existentes con `section_repo.import_from_csv()`
3. Importar preguntas existentes con `question_repo.import_from_json()`
