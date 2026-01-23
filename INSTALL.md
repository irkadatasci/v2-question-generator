# Guía de Instalación - Question Generator v2

## Prerrequisitos

- Python 3.9 o superior (para Python 3.8 ver solución de problemas)
- pip
- Cuenta en al menos uno de estos proveedores:
  - [Moonshot AI (Kimi)](https://platform.moonshot.cn/)
  - [Groq](https://groq.com/)
  - [OpenAI](https://platform.openai.com/)
  - O Ollama instalado localmente

## Instalación

### 1. Clonar/Navegar al proyecto

```bash
cd v2-question-generator
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# En macOS/Linux:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
# Instalación básica
pip install -e .

# O con requirements.txt
pip install -r requirements.txt

# Para desarrollo (incluye pytest, black, etc.)
pip install -e ".[dev]"
```

### 4. Descargar modelo de spaCy

```bash
python -m spacy download en_core_web_sm
```

### 5. Configurar variables de entorno

Crea un archivo `.env` en la raíz:

```bash
cp .env.example .env
```

Edita `.env` y añade tu API key:

```bash
# Elige UNO de estos (o varios si quieres cambiar entre ellos)
MOONSHOT_API_KEY=tu_api_key_aqui
# GROQ_API_KEY=tu_api_key_aqui
# OPENAI_API_KEY=tu_api_key_aqui
```

### 6. Crear archivo de configuración

```bash
qgen config init
```

Esto creará `config.json`. Puedes editarlo para ajustar parámetros.

## Verificación de Instalación

```bash
# Ver ayuda
qgen --help

# Ver configuración
qgen config show

# Ver proveedores disponibles
qgen config providers
```

## Uso Rápido

```bash
# Generar flashcards desde un PDF
qgen pipeline documento.pdf --type flashcard

# Ver más opciones
qgen pipeline --help
```

## Configuración Avanzada

### Múltiples proveedores

Puedes configurar varios proveedores en `.env` y cambiar entre ellos:

```bash
# Usar Kimi (por defecto)
qgen pipeline doc.pdf --type flashcard

# Usar Groq
qgen pipeline doc.pdf --type flashcard --provider groq

# Usar OpenAI
qgen pipeline doc.pdf --type flashcard --provider openai
```

### Ollama (local)

Si prefieres usar modelos locales:

```bash
# Instalar Ollama
# https://ollama.ai/download

# Descargar un modelo
ollama pull llama3.2

# Usar en Question Generator
qgen pipeline doc.pdf --provider ollama
```

### Ajustar configuración

Edita `config.json` para cambiar:

- Umbrales de clasificación
- Tamaño de batch
- Nivel de validación
- Rutas de salida

## Solución de Problemas

### Error: "Python 3.8 no soportado"

Si tienes Python 3.8, debes actualizar:

```bash
# macOS con Homebrew
brew install python@3.11

# Linux (Ubuntu/Debian)
sudo apt-get install python3.11 python3.11-venv

# Windows
# Descargar desde https://www.python.org/downloads/
```

Luego crea un nuevo entorno virtual:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Error: "No se pudo conectar con {provider}"

- Verifica que tu API key sea correcta
- Verifica que no tenga espacios extra
- Para Ollama: verifica que el servidor esté corriendo (`ollama serve`)

### Error: "Directorio de prompts no existe"

```bash
# Verifica que exista la carpeta prompts/
ls prompts/

# Si no existe, crea la estructura:
mkdir -p prompts/{flashcard,true_false,multiple_choice,cloze}
```

### Error al importar spacy

```bash
# Reinstalar spacy y descargar modelo
pip install -U spacy
python -m spacy download en_core_web_sm
```

### Tests fallando

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=src --cov-report=html
```

## Actualización

```bash
# Actualizar dependencias
pip install --upgrade -r requirements.txt

# Reinstalar el paquete
pip install -e .
```

## Desinstalación

```bash
# Desactivar entorno virtual
deactivate

# Eliminar entorno virtual
rm -rf venv

# Opcional: eliminar datos generados
rm -rf datos/
```

## Siguiente Paso

Lee [README.md](README.md) para ejemplos de uso completos.
