#!/usr/bin/env python3
"""
Script de demostración para generar todos los tipos de preguntas:
Flashcards, Verdadero/Falso y Opción Múltiple.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para tratar 'src' como paquete
sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.config import ConfigLoader
from src.infrastructure.llm import LLMServiceImpl
from src.infrastructure.llm.prompt_manager import PromptServiceImpl
from src.infrastructure.persistence import (
    SectionRepositoryCSV,
    QuestionRepositoryJSON,
    ExperimentRepositoryJSON,
)
from src.application.use_cases.generate_questions import GenerateQuestionsUseCase, GenerateQuestionsRequest
from src.domain.entities.question import QuestionType

def run_generation(generate_uc, document_id, q_type):
    print(f"\n🎯 Generando: {q_type.value.upper()}")
    print("-" * 30)
    
    request = GenerateQuestionsRequest(
        document_id=document_id,
        question_type=q_type,
        batch_size=2,  # Pequeño para la demo
        only_relevant=True,
    )
    
    result = generate_uc.execute(request)
    
    if result.success:
        print(f"✅ Éxito: {result.questions_generated} preguntas generadas.")
        print(f"   Válidas: {result.questions_valid}")
        print(f"   Costo: ${result.cost_usd:.4f}")
    else:
        print(f"❌ Error: {result.error_message}")
    
    return result

def main():
    print("🚀 DEMO: Generador Multitipo (Flashcards, V/F, MCQ)")
    print("=" * 60)
    
    # Cargar configuración
    loader = ConfigLoader(Path("config.json"))
    settings = loader.load()
    
    # Configurar LLM para usar Ollama con ministral-3:14b-cloud
    provider = "ollama_cloud"
    model_name = "ministral-3:14b-cloud"
    llm_settings = settings.get_llm_settings(provider)
    
    # Forzamos la API Key proporcionada por el usuario para la demo
    api_key = "32b78bb962f7423fbd33368b9a7f375a.97pxeZDls5Jq4Df6APafLuaw"
    
    print(f"🤖 Configurando LLM: {provider} ({model_name})")
    
    llm_service = LLMServiceImpl.from_config(
        provider=provider,
        api_key=api_key,
        model=model_name,
        temperature=llm_settings.temperature,
        max_tokens=llm_settings.max_tokens,
    )
    
    if not llm_service.verify_connection():
        print(f"❌ No se pudo conectar con {provider}. Revisa tu conexión u Ollama.")
        return

    # Usar un document_id conocido de los datos procesados
    document_id = "d62d5c591634" 
    
    # Repositorios
    # Apuntamos al directorio donde están los CSVs de preprocesamiento
    preproc_dir = settings.paths.intermediate_dir / "preprocesamiento"
    section_repo = SectionRepositoryCSV(preproc_dir)
    
    # Cargar el CSV más reciente para este documento
    latest_csv = section_repo.get_latest_csv(f"secciones_{document_id}*.csv")
    if latest_csv:
        print(f"📥 Cargando secciones desde: {latest_csv.name}")
        section_repo.load_from_csv(latest_csv, document_id)
    else:
        print(f"⚠️ No se encontró CSV de secciones en {preproc_dir}")
        return

    question_repo = QuestionRepositoryJSON(settings.paths.output_dir)
    experiment_repo = ExperimentRepositoryJSON(settings.paths.experiments_dir)
    prompt_service = PromptServiceImpl(prompts_path=settings.paths.prompts_dir)
    
    generate_uc = GenerateQuestionsUseCase(
        llm_service=llm_service,
        prompt_service=prompt_service,
        section_repository=section_repo,
        question_repository=question_repo,
        experiment_repository=experiment_repo,
    )
    
    # Generar los 3 tipos prioritarios
    types_to_generate = [
        QuestionType.FLASHCARD,
        QuestionType.TRUE_FALSE,
        QuestionType.MULTIPLE_CHOICE
    ]
    
    for q_type in types_to_generate:
        try:
            run_generation(generate_uc, document_id, q_type)
        except Exception as e:
            print(f"❌ Excepción generando {q_type.value}: {e}")

    print("\n" + "=" * 60)
    print("✨ Demo finalizada. Revisa la carpeta 'datos/procesadas' para ver los resultados.")

if __name__ == "__main__":
    main()
