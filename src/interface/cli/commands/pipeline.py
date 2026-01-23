"""
Pipeline Command - Comando para ejecutar pipeline completo.
"""

from pathlib import Path
from typing import List, Optional

from ....domain.entities.question import QuestionType
from ....infrastructure.config import Settings
from ....infrastructure.llm import LLMServiceImpl
from ....infrastructure.classification import SemanticClassificationService
from ....infrastructure.llm.prompt_manager import PromptServiceImpl
from ....infrastructure.pdf import PDFExtractorServiceImpl
from ....infrastructure.persistence import (
    SectionRepositoryCSV,
    QuestionRepositoryJSON,
    DocumentRepositoryJSON,
    ExperimentRepositoryJSON,
)
from ....application.use_cases import (
    ExtractSectionsUseCase,
    ClassifySectionsUseCase,
    GenerateQuestionsUseCase,
    ValidateQuestionsUseCase,
    RunPipelineUseCase,
    RunPipelineRequest,
)


class PipelineCommand:
    """Comando para ejecutar el pipeline completo."""

    def __init__(self, settings: Settings):
        """
        Args:
            settings: Configuración de la aplicación
        """
        self._settings = settings

    def execute(
        self,
        pdf_path: Path,
        question_type: str,
        provider: Optional[str] = None,
        skip_stages: List[str] = None,
        output_dir: Optional[Path] = None,
    ) -> int:
        """
        Ejecuta el pipeline completo.

        Args:
            pdf_path: Ruta al PDF
            question_type: Tipo de pregunta
            provider: Proveedor de LLM
            skip_stages: Etapas a omitir
            output_dir: Directorio de salida

        Returns:
            Código de salida
        """
        skip_stages = skip_stages or []

        print("=" * 60)
        print("🚀 QUESTION GENERATOR v2 - PIPELINE COMPLETO")
        print("=" * 60)

        # Verificar PDF
        if not pdf_path.exists():
            print(f"❌ Archivo no encontrado: {pdf_path}")
            return 1

        # Determinar proveedor
        provider = provider or self._settings.default_llm_provider
        llm_settings = self._settings.get_llm_settings(provider)

        if "generate" not in skip_stages and not llm_settings.is_configured():
            print(f"❌ Proveedor {provider} no está configurado")
            return 1

        q_type = QuestionType(question_type)

        print(f"\n📄 PDF: {pdf_path.name}")
        print(f"📝 Tipo: {question_type}")
        print(f"🤖 LLM: {provider}")
        print(f"⏭️  Skip: {skip_stages or 'ninguna'}")

        # Crear todos los servicios
        print("\n📦 Inicializando servicios...")

        pdf_extractor = PDFExtractorServiceImpl()
        document_repo = DocumentRepositoryJSON(
            self._settings.paths.intermediate_dir / "documents"
        )
        section_repo = SectionRepositoryCSV(
            self._settings.paths.intermediate_dir / "sections"
        )
        question_repo = QuestionRepositoryJSON(
            output_dir or self._settings.paths.output_dir
        )
        experiment_repo = ExperimentRepositoryJSON(
            self._settings.paths.experiments_dir
        )

        # Crear casos de uso
        extract_uc = ExtractSectionsUseCase(
            pdf_extractor=pdf_extractor,
            document_repository=document_repo,
            section_repository=section_repo,
        )

        classification_service = SemanticClassificationService(
            threshold_relevant=self._settings.classification.threshold_relevant,
            threshold_review=self._settings.classification.threshold_review,
            auto_conserve_length=self._settings.classification.auto_conserve_length,
        )

        classify_uc = ClassifySectionsUseCase(
            classification_service=classification_service,
            section_repository=section_repo,
        )

        # LLM service (solo si no se omite generación)
        llm_service = None
        prompt_service = None

        if "generate" not in skip_stages:
            try:
                llm_service = LLMServiceImpl.from_config(
                    provider=provider,
                    api_key=llm_settings.api_key,
                    model=llm_settings.model,
                    temperature=llm_settings.temperature,
                    max_tokens=llm_settings.max_tokens,
                )

                prompt_service = PromptServiceImpl(
                    prompts_path=self._settings.paths.prompts_dir,
                )

                print("   ✓ Verificando conexión LLM...")
                if not llm_service.verify_connection():
                    print(f"   ❌ No se pudo conectar con {provider}")
                    return 1
                print("   ✓ Conexión LLM exitosa")

            except Exception as e:
                print(f"   ❌ Error inicializando LLM: {e}")
                return 1

        generate_uc = GenerateQuestionsUseCase(
            llm_service=llm_service,
            prompt_service=prompt_service,
            section_repository=section_repo,
            question_repository=question_repo,
            experiment_repository=experiment_repo,
        ) if llm_service else None

        validate_uc = ValidateQuestionsUseCase(
            question_repository=question_repo,
        )

        # Crear pipeline
        pipeline_uc = RunPipelineUseCase(
            extract_use_case=extract_uc,
            classify_use_case=classify_uc,
            generate_use_case=generate_uc,
            validate_use_case=validate_uc,
        )

        # Ejecutar
        print("\n" + "=" * 60)
        print("🔄 EJECUTANDO PIPELINE")
        print("=" * 60)

        request = RunPipelineRequest(
            pdf_path=pdf_path,
            question_type=q_type,
            threshold_relevant=self._settings.classification.threshold_relevant,
            batch_size=self._settings.generation.default_batch_size,
            auto_adjust_batch_size=self._settings.generation.auto_adjust_batch_size,
            validation_level=self._settings.generation.validation_level,
            auto_fix=self._settings.generation.auto_fix_questions,
            skip_stages=skip_stages,
            stop_on_error=True,
        )

        result = pipeline_uc.execute(request)

        # Mostrar resultados por etapa
        print("\n" + "-" * 60)
        print("📊 RESULTADOS POR ETAPA")
        print("-" * 60)

        for stage in result.stages:
            status = "✅" if stage.success else "❌"
            print(f"\n{status} {stage.stage_name.upper()}")
            print(f"   Tiempo: {stage.execution_time_seconds:.2f}s")

            if stage.error_message:
                print(f"   Error: {stage.error_message}")

            # Detalles específicos por etapa
            if stage.stage_name == "extract":
                print(f"   Secciones: {stage.details.get('total_sections', 0)}")
            elif stage.stage_name == "classify":
                print(f"   Relevantes: {stage.details.get('sections_relevant', 0)}")
            elif stage.stage_name == "generate":
                print(f"   Preguntas: {stage.details.get('questions_generated', 0)}")
                print(f"   Costo: ${stage.details.get('cost_usd', 0):.4f}")
            elif stage.stage_name == "validate":
                print(f"   Válidas: {stage.details.get('valid_questions', 0)}")

        # Resumen final
        print("\n" + "=" * 60)
        print("📈 RESUMEN FINAL")
        print("=" * 60)

        if result.success:
            print(f"\n✅ Pipeline completado exitosamente")
        else:
            print(f"\n❌ Pipeline falló: {result.error_message}")

        print(f"\n   📄 Documento: {result.document_id}")
        print(f"   📝 Secciones totales: {result.total_sections}")
        print(f"   ✓ Secciones relevantes: {result.sections_relevant}")
        print(f"   ❓ Preguntas generadas: {result.questions_generated}")
        print(f"   ✓ Preguntas válidas: {result.questions_valid}")
        print(f"   🎫 Tokens usados: {result.total_tokens:,}")
        print(f"   💰 Costo total: ${result.total_cost_usd:.4f}")
        print(f"   ⏱️  Tiempo total: {result.total_execution_time_seconds:.2f}s")

        if result.output_paths:
            print(f"\n   📁 Archivos generados:")
            for name, path in result.output_paths.items():
                print(f"      - {name}: {path}")

        print("\n" + "=" * 60)

        return 0 if result.success else 1
