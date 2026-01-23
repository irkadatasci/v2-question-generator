"""
Quick Start - Ejemplo de uso básico de Question Generator v2.

Este script demuestra cómo usar el pipeline completo para generar
preguntas desde un PDF.
"""

from pathlib import Path
from src.infrastructure.config import ConfigLoader
from src.infrastructure import (
    LLMServiceImpl,
    PDFExtractorServiceImpl,
    SemanticClassificationService,
    SectionRepositoryCSV,
    QuestionRepositoryJSON,
    DocumentRepositoryJSON,
    ExperimentRepositoryJSON,
)
from src.infrastructure.llm.prompt_manager import PromptServiceImpl
from src.application.use_cases import (
    ExtractSectionsUseCase,
    ExtractSectionsRequest,
    ClassifySectionsUseCase,
    ClassifySectionsRequest,
    GenerateQuestionsUseCase,
    GenerateQuestionsRequest,
)
from src.domain.entities.question import QuestionType


def main():
    """Ejecuta el pipeline completo."""
    # 1. Cargar configuración
    print("📦 Cargando configuración...")
    loader = ConfigLoader()
    settings = loader.load()

    # Validar configuración
    is_valid, errors = settings.validate()
    if not is_valid:
        print("❌ Errores de configuración:")
        for error in errors:
            print(f"   - {error}")
        return

    # 2. Configurar rutas
    pdf_path = Path("documento.pdf")  # Cambiar por tu PDF
    if not pdf_path.exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        print("   Crea un archivo 'documento.pdf' o cambia la ruta en el script")
        return

    # 3. Crear servicios de infraestructura
    print("🔧 Inicializando servicios...")

    pdf_extractor = PDFExtractorServiceImpl()
    classification_service = SemanticClassificationService(
        threshold_relevant=settings.classification.threshold_relevant,
        threshold_review=settings.classification.threshold_review,
        auto_conserve_length=settings.classification.auto_conserve_length,
    )

    # Repositorios
    document_repo = DocumentRepositoryJSON(settings.paths.intermediate_dir / "documents")
    section_repo = SectionRepositoryCSV(settings.paths.intermediate_dir / "sections")
    question_repo = QuestionRepositoryJSON(settings.paths.output_dir)
    experiment_repo = ExperimentRepositoryJSON(settings.paths.experiments_dir)

    # LLM y Prompts
    llm_settings = settings.get_llm_settings()
    llm_service = LLMServiceImpl.from_config(
        provider=llm_settings.provider,
        api_key=llm_settings.api_key,
        model=llm_settings.model,
        temperature=llm_settings.temperature,
        max_tokens=llm_settings.max_tokens,
    )

    prompt_service = PromptServiceImpl(settings.paths.prompts_dir)

    # 4. Crear casos de uso
    extract_uc = ExtractSectionsUseCase(
        pdf_extractor=pdf_extractor,
        document_repository=document_repo,
        section_repository=section_repo,
    )

    classify_uc = ClassifySectionsUseCase(
        classification_service=classification_service,
        section_repository=section_repo,
    )

    generate_uc = GenerateQuestionsUseCase(
        llm_service=llm_service,
        prompt_service=prompt_service,
        section_repository=section_repo,
        question_repository=question_repo,
        experiment_repository=experiment_repo,
    )

    # 5. ETAPA 1: Extraer secciones
    print("\n" + "=" * 60)
    print("📄 ETAPA 1: EXTRACCIÓN DE SECCIONES")
    print("=" * 60)

    extract_result = extract_uc.execute(ExtractSectionsRequest(
        pdf_path=pdf_path,
        save_to_csv=True,
    ))

    if not extract_result.success:
        print(f"❌ Error: {extract_result.error_message}")
        return

    document_id = extract_result.document.id
    print(f"✅ Extracción completada")
    print(f"   Páginas: {extract_result.total_pages}")
    print(f"   Secciones: {extract_result.total_sections}")
    print(f"   Document ID: {document_id}")

    # 6. ETAPA 2: Clasificar secciones
    print("\n" + "=" * 60)
    print("🔍 ETAPA 2: CLASIFICACIÓN SEMÁNTICA")
    print("=" * 60)

    classify_result = classify_uc.execute(ClassifySectionsRequest(
        document_id=document_id,
        threshold_relevant=settings.classification.threshold_relevant,
        threshold_review=settings.classification.threshold_review,
    ))

    if not classify_result.success:
        print(f"❌ Error: {classify_result.error_message}")
        return

    print(f"✅ Clasificación completada")
    print(f"   Secciones clasificadas: {classify_result.sections_classified}")
    print(f"   Relevantes: {classify_result.sections_relevant}")
    print(f"   Descartadas: {classify_result.sections_discarded}")

    # 7. ETAPA 3: Generar preguntas
    print("\n" + "=" * 60)
    print("🤖 ETAPA 3: GENERACIÓN DE PREGUNTAS")
    print("=" * 60)

    # Verificar conexión LLM
    print("   Verificando conexión con LLM...")
    if not llm_service.verify_connection():
        print(f"❌ No se pudo conectar con {llm_settings.provider}")
        return
    print("   ✓ Conexión exitosa")

    generate_result = generate_uc.execute(GenerateQuestionsRequest(
        document_id=document_id,
        question_type=QuestionType.FLASHCARD,  # Cambiar según necesites
        batch_size=settings.generation.default_batch_size,
        only_relevant=settings.generation.only_relevant_sections,
        auto_adjust_batch_size=settings.generation.auto_adjust_batch_size,
    ))

    if not generate_result.success:
        print(f"❌ Error: {generate_result.error_message}")
        return

    print(f"✅ Generación completada")
    print(f"   Preguntas generadas: {generate_result.questions_generated}")
    print(f"   Válidas: {generate_result.questions_valid}")
    print(f"   Inválidas: {generate_result.questions_invalid}")
    print(f"   Tokens: {generate_result.tokens_used:,}")
    print(f"   Costo: ${generate_result.cost_usd:.4f}")
    print(f"   Archivo: {generate_result.output_json_path}")

    # 8. Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)
    print(f"✅ Pipeline completado exitosamente")
    print(f"   Documento: {document_id}")
    print(f"   Preguntas generadas: {generate_result.questions_generated}")
    print(f"   Archivo de salida: {generate_result.output_json_path}")
    print("\n💡 Siguiente paso:")
    print(f"   qgen validate {document_id} --level moderate --fix")


if __name__ == "__main__":
    main()
