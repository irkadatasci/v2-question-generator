import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Asegurar que el root está en el path
sys.path.append(str(Path.cwd()))

from src.infrastructure.llm.backends.lmstudio import LMStudioBackend
from src.infrastructure.llm.backends.base import LLMConfig

# Cargar .env para obtener la configuración real
load_dotenv()

model = os.getenv("LMSTUDIO_MODEL", "Ministral 3 14B Reasoning")
url = os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1")

print(f"Probando con modelo: {model}")
print(f"Probando con URL: {url}")

config = LLMConfig(
    api_key="lm-studio",
    model=model,
    base_url=url,
    temperature=0.7,
    max_tokens=2000
)

backend = LMStudioBackend(config)
try:
    print("Enviando petición...")
    response = backend.generate(
        prompt="Genera una lista con 1 flashcard sobre 'La Costumbre'. Responde en JSON con la llave 'preguntas'.",
        system_prompt="Actúa como un generador de preguntas JSON."
    )
    print("\n--- RAW CONTENT ---")
    print(response.raw_content)
    print("\n--- CONTENT ---")
    print(response.content)
except Exception as e:
    print(f"Error: {e}")
