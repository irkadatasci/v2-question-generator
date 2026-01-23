#!/usr/bin/env python3
"""
Script de debug para la generación de preguntas.
"""

import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.config import ConfigLoader
from infrastructure.llm import LLMServiceImpl
from infrastructure.llm.prompt_manager import PromptServiceImpl
from infrastructure.persistence import (
    SectionRepositoryCSV,
    QuestionRepositoryJSON,
    ExperimentRepositoryJSON,
)
from application.use_cases.generate_questions import GenerateQuestionsUseCase, GenerateQuestionsRequest
from domain.entities.question import QuestionType
import json

def main():
    print("🔍 DEBUG: Generación de preguntas")
    print("=" * 50)
    
    # Cargar configuración
    config_path = Path("config.json")
    loader = ConfigLoader(config_path)
    settings = loader.load()
    
    print(f"✅ Configuración cargada")
    
    # Configurar LLM
    provider = "ollama_cloud"
    llm_settings = settings.get_llm_settings(provider)
    
    print(f"🤖 Configurando LLM: {provider}")
    print(f"   Model: {llm_settings.model}")
    print(f"   API Key configurada: {'Sí' if llm_settings.api_key else 'No'}")
    
    llm_service = LLMServiceImpl.from_config(
        provider=provider,
        api_key=llm_settings.api_key,
        model=llm_settings.model,
        temperature=llm_settings.temperature,
        max_tokens=llm_settings.max_tokens,
    )
    
    # Verificar conexión
    print(f"🔌 Verificando conexión...")
    if not llm_service.verify_connection():
        print("❌ No se pudo conectar con el LLM")
        return
    
    print("✅ Conexión exitosa")
    
    # Configurar repositorios
    document_id = "d62d5c591634"
    
    section_repo = SectionRepositoryCSV(
        settings.paths.intermediate_dir / "sections"
    )
    question_repo = QuestionRepositoryJSON(
        settings.paths.output_dir
    )
    experiment_repo = ExperimentRepositoryJSON(
        settings.paths.experiments_dir
    )
    
    # Cargar secciones
    sections = section_repo.find_relevant(document_id)
    print(f"📄 Secciones cargadas: {len(sections)}")
    
    if not sections:
        print("❌ No hay secciones para procesar")
        return
    
    # Mostrar primera sección como ejemplo
    if sections:
        first_section = sections[0]
        print(f"📝 Ejemplo de sección:")
        print(f"   Título: {first_section.title}")
        print(f"   Página: {first_section.page}")
        print(f"   Longitud: {first_section.text_length} caracteres")
        print(f"   Texto: {first_section.text[:200]}...")
    
    # Configurar prompt service
    prompt_service = PromptServiceImpl(
        prompts_path=settings.paths.prompts_dir,
    )
    
    # Crear caso de uso
    generate_uc = GenerateQuestionsUseCase(
        llm_service=llm_service,
        prompt_service=prompt_service,
        section_repository=section_repo,
        question_repository=question_repo,
        experiment_repository=experiment_repo,
    )
    
    # Crear request
    request = GenerateQuestionsRequest(
        document_id=document_id,
        question_type=QuestionType.FLASHCARD,
        batch_size=2,  # Batch pequeño para debug
        only_relevant=True,
        auto_adjust_batch_size=False,
    )
    
    print(f"🎯 Ejecutando generación...")
    print(f"   Tipo: {request.question_type.value}")
    print(f"   Batch size: {request.batch_size}")
    print(f"   Solo relevantes: {request.only_relevant}")
    
    # Ejecutar
    result = generate_uc.execute(request)
    
    print(f"\n📊 RESULTADO:")
    print(f"   Éxito: {'Sí' if result.success else 'No'}")
    print(f"   Secciones procesadas: {result.total_sections}")
    print(f"   Batches: {result.total_batches}")
    print(f"   Batches exitosos: {result.batches_successful}")
    print(f"   Batches fallidos: {result.batches_failed}")
    print(f"   Preguntas generadas: {result.questions_generated}")
    print(f"   Preguntas válidas: {result.questions_valid}")
    print(f"   Tokens usados: {result.tokens_used}")
    print(f"   Costo: ${result.cost_usd:.4f}")
    print(f"   Tiempo: {result.execution_time_seconds:.2f}s")
    
    if result.error_message:
        print(f"   Error: {result.error_message}")
    
    if result.output_json_path:
        print(f"   Archivo de salida: {result.output_json_path}")
    
    # Verificar preguntas en repositorio
    print(f"\n🔍 Verificando repositorio de preguntas...")
    questions_in_repo = question_repo.find_all(document_id)
    print(f"   Preguntas en repositorio: {len(questions_in_repo)}")
    
    if questions_in_repo:
        print(f"   Ejemplo de pregunta:")
        first_q = questions_in_repo[0]
        print(f"      ID: {first_q.id}")
        print(f"      Tipo: {first_q.type.value}")
        print(f"      Texto: {first_q.question_text[:100]}...")

if __name__ == "__main__":
    main()