"""
Generate Command - Comando para generar preguntas.
"""

from typing import Optional

from ....domain.entities.question import QuestionType
from ....infrastructure.config import Settings
from ....infrastructure.llm import LLMServiceImpl
from ....infrastructure.llm.prompt_manager import PromptServiceImpl
from ....infrastructure.persistence import (
    SectionRepositoryCSV,
    QuestionRepositoryJSON,
    ExperimentRepositoryJSON,
)
from ....application.use_cases import GenerateQuestionsUseCase, GenerateQuestionsRequest


class GenerateCommand:
    """Comando para generar preguntas con LLM."""

    def __init__(self, settings: Settings):
        """
        Args:
            settings: Configuración de la aplicación
        """
        self._settings = settings

    def execute(
        self,
        document_id: str,
        question_type: str,
        provider: Optional[str] = None,
        batch_size: int = 5,
    ) -> int:
        """
        Ejecuta la generación de preguntas.

        Args:
            document_id: ID del documento
            question_type: Tipo de pregunta
            provider: Proveedor de LLM
            batch_size: Tamaño de batch

        Returns:
            Código de salida
        """
        # Determinar proveedor
        provider = provider or self._settings.default_llm_provider
        llm_settings = self._settings.get_llm_settings(provider)

        if not llm_settings.is_configured():
            print(f"❌ Proveedor {provider} no está configurado")
            print(f"   Configure la variable de entorno correspondiente")
            return 1

        try:
            q_type = QuestionType[question_type.upper()]
        except KeyError:
            try:
                q_type = QuestionType(question_type)
            except ValueError:
                print(f"❌ Tipo de pregunta desconocido: {question_type}")
                return 1
        print(f"🤖 Generando preguntas tipo '{question_type}'")
        print(f"   Proveedor: {provider}")
        print(f"   Modelo: {llm_settings.model or 'default'}")
        print(f"   Documento: {document_id}")

        # Crear servicios
        try:
            llm_service = LLMServiceImpl.from_config(
                provider=provider,
                api_key=llm_settings.api_key,
                model=llm_settings.model,
                temperature=llm_settings.temperature,
                max_tokens=llm_settings.max_tokens,
                timeout=llm_settings.timeout,
            )
        except Exception as e:
            print(f"❌ Error inicializando LLM: {e}")
            return 1

        prompt_service = PromptServiceImpl(
            prompts_path=self._settings.paths.prompts_dir,
        )

        section_repo = SectionRepositoryCSV(
            self._settings.paths.intermediate_dir / "sections"
        )
        question_repo = QuestionRepositoryJSON(
            self._settings.paths.output_dir
        )
        experiment_repo = ExperimentRepositoryJSON(
            self._settings.paths.experiments_dir
        )

        # Verificar conexión
        print("   Verificando conexión con LLM...")
        if not llm_service.verify_connection():
            print(f"❌ No se pudo conectar con {provider}")
            return 1
        print("   ✓ Conexión exitosa")

        # Crear caso de uso
        use_case = GenerateQuestionsUseCase(
            llm_service=llm_service,
            prompt_service=prompt_service,
            section_repository=section_repo,
            question_repository=question_repo,
            experiment_repository=experiment_repo,
        )

        # Ejecutar
        request = GenerateQuestionsRequest(
            document_id=document_id,
            question_type=q_type,
            batch_size=batch_size,
            only_relevant=self._settings.generation.only_relevant_sections,
            auto_adjust_batch_size=self._settings.generation.auto_adjust_batch_size,
        )

        print("   Procesando secciones...")
        result = use_case.execute(request)

        if result.success:
            print(f"\n✅ Generación completada")
            print(f"   📊 Secciones procesadas: {result.total_sections}")
            print(f"   📦 Batches: {result.batches_successful}/{result.total_batches}")
            print(f"   ❓ Preguntas generadas: {result.questions_generated}")
            print(f"   ✓ Válidas: {result.questions_valid}")
            print(f"   ✗ Inválidas: {result.questions_invalid}")
            print(f"   🎫 Tokens: {result.tokens_used:,}")
            print(f"   💰 Costo: ${result.cost_usd:.4f}")
            print(f"   📁 JSON: {result.output_json_path}")
            print(f"   🧪 Experimento: {result.experiment_id}")
            print(f"   ⏱️  Tiempo: {result.execution_time_seconds:.2f}s")
            return 0
        else:
            print(f"❌ Error: {result.error_message}")
            return 1
