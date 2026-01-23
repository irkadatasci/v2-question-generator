#!/usr/bin/env python3
"""
Script de prueba mejorado para extrapolar Flashcards a Multiple Choice.
INCLUYE PROTECCIÓN ANTI-ALUCINACIÓN (GROUNDING).
"""
import sys
import json
import re
from pathlib import Path

# Agregar raíz
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.config import ConfigLoader
from src.infrastructure.llm import LLMServiceImpl

def extract_json(text):
    """Intenta extraer un bloque JSON del texto."""
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def main():
    print("🧪 TEST: Extrapolación FC -> MC (Con Grounding)")
    print("=" * 60)
    
    loader = ConfigLoader(Path("config.json"))
    settings = loader.load()
    
    # Configuración manual
    api_key = "32b78bb962f7423fbd33368b9a7f375a.97pxeZDls5Jq4Df6APafLuaw"
    provider = "ollama_cloud"
    llm_settings = settings.get_llm_settings(provider)
    
    base_url = llm_settings.get("base_url") if isinstance(llm_settings, dict) else getattr(llm_settings, "base_url", "https://ollama.com/api")

    llm_service = LLMServiceImpl.from_config(
        provider=provider,
        api_key=api_key,
        model="ministral-3:14b-cloud",
        temperature=0.1, # Temperatura MUY baja para evitar invenciones
        max_tokens=2000,
        base_url=base_url
    )

    # DATOS DE ENTRADA
    # 1. El texto fuente real (limitado)
    source_text = """
El dolo consiste en la intención positiva de inferir injuria a la persona o propiedad de otro (Art. 44 CC).
El efecto principal es que el deudor doloso responde de todos los perjuicios, tanto previstos como imprevistos, que sean consecuencia directa del incumplimiento (Art. 1558 CC).
A diferencia de la culpa, el dolo no se puede presumir y debe probarse siempre por quien lo alega (Art. 1459 CC), salvo los casos en que la ley expresamente lo presume.
"""

    # 2. La Flashcard derivada
    fc_anverso = "Dolo vs culpa: ¿qué diferencia clave existe?"
    fc_reverso = "El dolo no se presume y debe probarse siempre por quien lo alega."
    
    print(" SOURCE TEXT:")
    print(f"'{source_text.strip()}'")
    print("\n INPUT FLASHCARD:")
    print(f"P: {fc_anverso}")
    print(f"R: {fc_reverso}")
    print("-" * 30)

    # Prompt con Grounding
    system_prompt = "Eres un experto en psicometría. Tu salida debe ser estrictamente JSON."
    prompt = f"""
CONVIERTE ESTA FLASHCARD EN UN ÍTEM DE SELECCIÓN MÚLTIPLE.

CONTEXTO FUENTE (ÚNICA VERDAD):
"{source_text}"

PREGUNTA BASE: "{fc_anverso}"
VERDAD A DEFENDER: "{fc_reverso}"

INSTRUCCIONES:
1. Crea un enunciado claro (stem).
2. Crea 1 opción correcta y 3 distractores plausibles.
3. GROUNDING ESTRICTO:
   - La justificación debe basarse ESTRÍCTAMENTE en el "CONTEXTO FUENTE".
   - ⛔️ PROHIBIDO citar autores (Mir Puig, etc), leyes o doctrinas que NO estén en el texto.
   - Si citas un artículo, debe ser uno de los mencionados en el texto (44, 1558, 1459).

FORMATO JSON:
{{
  "pregunta": "...",
  "opciones": ["...", "...", "...", "..."],
  "respuesta_correcta": 0,
  "justificacion": "..."
}}
"""

    print("⏳ Extrapolando con Grounding...")
    response = llm_service.generate(prompt, system_prompt=system_prompt, response_format="text")
    
    try:
        json_str = extract_json(response.content)
        data = json.loads(json_str)
        # Normalizar claves
        data = {k.lower(): v for k, v in data.items()}
        if 'item' in data and isinstance(data['item'], dict):
            data = {k.lower(): v for k, v in data['item'].items()}

        print("\n✅ RESULTADO MC (Grounding Check):")
        print(f"Enunciado: {data.get('pregunta')}")
        print("Opciones:")
        opciones = data.get('opciones', [])
        for i, opt in enumerate(opciones):
            marker = "✅" if i == data.get('respuesta_correcta') else "❌"
            print(f"  {marker} {i}) {opt}")
        print(f"Justificación: {data.get('justificacion')}")
        
    except Exception as e:
        print(f"❌ Error procesando respuesta: {e}")
        print("Raw content:")
        print(response.content)

if __name__ == "__main__":
    main()
