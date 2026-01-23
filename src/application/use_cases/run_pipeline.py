"""
Run Pipeline Use Case - Ejecuta el pipeline completo de generación.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ...domain.entities.question import QuestionType
from .extract_sections import ExtractSectionsUseCase, ExtractSectionsRequest, ExtractSectionsResult
from .classify_sections import ClassifySectionsUseCase, ClassifySectionsRequest, ClassifySectionsResult
from .generate_questions import GenerateQuestionsUseCase, GenerateQuestionsRequest, GenerateQuestionsResult
from .validate_questions import ValidateQuestionsUseCase, ValidateQuestionsRequest, ValidateQuestionsResult


@dataclass
class PipelineStageResult:
    """Resultado de una etapa del pipeline."""
    stage_name: str
    success: bool
    execution_time_seconds: float
    details: Dict = field(default_factory=dict)
    error_message: str = ""


@dataclass
class RunPipelineRequest:
    """Request para ejecutar el pipeline completo."""
    pdf_path: Path
    question_type: QuestionType

    # Parámetros de extracción (Etapa 1)
    save_extraction_csv: bool = True

    # Parámetros de clasificación (Etapa 2)
    threshold_relevant: float = 0.7
    threshold_review: float = 0.5
    auto_conserve_length: int = 300

    # Parámetros de generación (Etapa 3)
    batch_size: int = 5
    only_relevant: bool = True
    auto_adjust_batch_size: bool = True

    # Parámetros de validación (Etapa 4)
    validation_level: str = "moderate"
    auto_fix: bool = True

    # Control de ejecución
    skip_stages: List[str] = field(default_factory=list)
    stop_on_error: bool = True
    experiment_tags: Optional[dict] = None


@dataclass
class RunPipelineResult:
    """Resultado de la ejecución del pipeline."""
    success: bool
    document_id: str = ""

    # Resultados por etapa
    stages: List[PipelineStageResult] = field(default_factory=list)

    # Resumen
    total_sections: int = 0
    sections_relevant: int = 0
    questions_generated: int = 0
    questions_valid: int = 0

    # Costos y tiempos
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_execution_time_seconds: float = 0.0

    # Rutas de salida
    output_paths: Dict[str, Path] = field(default_factory=dict)

    error_message: str = ""


class RunPipelineUseCase:
    """
    Caso de uso: Ejecutar pipeline completo de generación.

    Orquesta las 4 etapas del pipeline:
    1. Extracción de secciones del PDF
    2. Clasificación semántica de secciones
    3. Generación de preguntas con LLM
    4. Validación de preguntas generadas

    Este caso de uso actúa como facade para el pipeline completo,
    permitiendo ejecutar todo el proceso con una sola llamada.
    """

    def __init__(
        self,
        extract_use_case: ExtractSectionsUseCase,
        classify_use_case: ClassifySectionsUseCase,
        generate_use_case: GenerateQuestionsUseCase,
        validate_use_case: ValidateQuestionsUseCase,
    ):
        """
        Args:
            extract_use_case: Caso de uso de extracción
            classify_use_case: Caso de uso de clasificación
            generate_use_case: Caso de uso de generación
            validate_use_case: Caso de uso de validación
        """
        self._extract = extract_use_case
        self._classify = classify_use_case
        self._generate = generate_use_case
        self._validate = validate_use_case

    def execute(self, request: RunPipelineRequest) -> RunPipelineResult:
        """
        Ejecuta el pipeline completo.

        Args:
            request: Request con parámetros del pipeline

        Returns:
            RunPipelineResult con el resultado completo
        """
        start_time = datetime.now()
        stages: List[PipelineStageResult] = []
        output_paths: Dict[str, Path] = {}
        document_id = ""

        try:
            # ═══════════════════════════════════════════════════════════
            # ETAPA 1: EXTRACCIÓN DE SECCIONES
            # ═══════════════════════════════════════════════════════════
            if "extract" not in request.skip_stages:
                extract_result = self._run_extraction(request)
                stages.append(extract_result)

                if not extract_result.success and request.stop_on_error:
                    return self._build_error_result(
                        stages, start_time,
                        f"Pipeline falló en extracción: {extract_result.error_message}"
                    )

                document_id = extract_result.details.get("document_id", "")
                if extract_result.details.get("output_csv"):
                    output_paths["extraction_csv"] = extract_result.details["output_csv"]

            else:
                # Si se omite la extracción, cargar datos existentes
                print("📥 Cargando datos existentes...")
                document_id, loaded_sections = self._load_existing_data(request.pdf_path)
                if not document_id:
                    return self._build_error_result(
                        stages, start_time,
                        "No se pudieron cargar datos existentes para el documento"
                    )
                print(f"✓ Cargadas {loaded_sections} secciones para documento {document_id}")

            # ═══════════════════════════════════════════════════════════
            # ETAPA 2: CLASIFICACIÓN SEMÁNTICA
            # ═══════════════════════════════════════════════════════════
            if "classify" not in request.skip_stages:
                classify_result = self._run_classification(request, document_id)
                stages.append(classify_result)

                if not classify_result.success and request.stop_on_error:
                    return self._build_error_result(
                        stages, start_time,
                        f"Pipeline falló en clasificación: {classify_result.error_message}"
                    )

                if classify_result.details.get("output_csv"):
                    output_paths["classification_csv"] = classify_result.details["output_csv"]

            # ═══════════════════════════════════════════════════════════
            # ETAPA 3: GENERACIÓN DE PREGUNTAS
            # ═══════════════════════════════════════════════════════════
            if "generate" not in request.skip_stages:
                generate_result = self._run_generation(request, document_id)
                stages.append(generate_result)

                if not generate_result.success and request.stop_on_error:
                    return self._build_error_result(
                        stages, start_time,
                        f"Pipeline falló en generación: {generate_result.error_message}"
                    )

                if generate_result.details.get("output_json"):
                    output_paths["generation_json"] = generate_result.details["output_json"]

            # ═══════════════════════════════════════════════════════════
            # ETAPA 4: VALIDACIÓN DE PREGUNTAS
            # ═══════════════════════════════════════════════════════════
            if "validate" not in request.skip_stages:
                validate_result = self._run_validation(request, document_id)
                stages.append(validate_result)

                if not validate_result.success and request.stop_on_error:
                    return self._build_error_result(
                        stages, start_time,
                        f"Pipeline falló en validación: {validate_result.error_message}"
                    )

                if validate_result.details.get("output_invalid"):
                    output_paths["invalid_json"] = validate_result.details["output_invalid"]

            # ═══════════════════════════════════════════════════════════
            # RESULTADO FINAL
            # ═══════════════════════════════════════════════════════════
            total_time = (datetime.now() - start_time).total_seconds()

            return RunPipelineResult(
                success=True,
                document_id=document_id,
                stages=stages,
                total_sections=self._get_stage_detail(stages, "extract", "total_sections", 0),
                sections_relevant=self._get_stage_detail(stages, "classify", "sections_relevant", 0),
                questions_generated=self._get_stage_detail(stages, "generate", "questions_generated", 0),
                questions_valid=self._get_stage_detail(stages, "validate", "valid_questions", 0),
                total_tokens=self._get_stage_detail(stages, "generate", "tokens_used", 0),
                total_cost_usd=self._get_stage_detail(stages, "generate", "cost_usd", 0.0),
                total_execution_time_seconds=total_time,
                output_paths=output_paths,
            )

        except Exception as e:
            return self._build_error_result(
                stages, start_time,
                f"Error inesperado en pipeline: {e}"
            )

    def _load_existing_data(self, pdf_path: Path) -> tuple[str, int]:
        """
        Carga datos existentes desde CSV cuando se omite la extracción.
        
        Args:
            pdf_path: Ruta del PDF
            
        Returns:
            Tupla con (document_id, número_de_secciones_cargadas)
        """
        import hashlib
        from pathlib import Path
        
        # Calcular document_id igual que en ExtractSectionsUseCase
        document_id = hashlib.md5(str(pdf_path).encode()).hexdigest()[:12]
        
        # Buscar el CSV más reciente para este documento
        sections_dir = pdf_path.parent.parent / "datos" / "intermediate" / "preprocesamiento"
        pattern = f"secciones_{document_id[:12]}*"
        
        import glob
        files = glob.glob(str(sections_dir / pattern))
        if not files:
            print(f"❌ No se encontró archivo CSV para documento {document_id}")
            return "", 0
        
        # Obtener el archivo más reciente
        latest_file = max(files, key=lambda f: Path(f).stat().st_mtime)
        
        try:
            # Cargar en el repositorio de secciones
            section_repo = self._extract._sections
            loaded_sections = section_repo.load_from_csv(Path(latest_file), document_id)
            return document_id, len(loaded_sections)
        except Exception as e:
            print(f"❌ Error cargando datos existentes: {e}")
            return "", 0

    def _run_extraction(self, request: RunPipelineRequest) -> PipelineStageResult:
        """Ejecuta la etapa de extracción."""
        stage_start = datetime.now()

        extract_request = ExtractSectionsRequest(
            pdf_path=request.pdf_path,
            save_to_csv=request.save_extraction_csv,
        )

        result = self._extract.execute(extract_request)
        stage_time = (datetime.now() - stage_start).total_seconds()

        return PipelineStageResult(
            stage_name="extract",
            success=result.success,
            execution_time_seconds=stage_time,
            details={
                "document_id": result.document.id if result.document else "",
                "total_pages": result.total_pages,
                "total_sections": result.total_sections,
                "output_csv": result.output_csv_path,
            },
            error_message=result.error_message,
        )

    def _run_classification(
        self,
        request: RunPipelineRequest,
        document_id: str,
    ) -> PipelineStageResult:
        """Ejecuta la etapa de clasificación."""
        stage_start = datetime.now()

        classify_request = ClassifySectionsRequest(
            document_id=document_id,
            threshold_relevant=request.threshold_relevant,
            threshold_review=request.threshold_review,
            auto_conserve_length=request.auto_conserve_length,
        )

        result = self._classify.execute(classify_request)
        stage_time = (datetime.now() - stage_start).total_seconds()

        return PipelineStageResult(
            stage_name="classify",
            success=result.success,
            execution_time_seconds=stage_time,
            details={
                "sections_classified": result.sections_classified,
                "sections_relevant": result.sections_relevant,
                "sections_discarded": result.sections_discarded,
                "average_score": result.average_score,
                "classification_counts": result.classification_counts,
                "output_csv": result.output_csv_path,
            },
            error_message=result.error_message,
        )

    def _run_generation(
        self,
        request: RunPipelineRequest,
        document_id: str,
    ) -> PipelineStageResult:
        """Ejecuta la etapa de generación."""
        stage_start = datetime.now()

        generate_request = GenerateQuestionsRequest(
            document_id=document_id,
            question_type=request.question_type,
            batch_size=request.batch_size,
            only_relevant=request.only_relevant,
            auto_adjust_batch_size=request.auto_adjust_batch_size,
            experiment_tags=request.experiment_tags,
        )

        result = self._generate.execute(generate_request)
        stage_time = (datetime.now() - stage_start).total_seconds()

        return PipelineStageResult(
            stage_name="generate",
            success=result.success,
            execution_time_seconds=stage_time,
            details={
                "experiment_id": result.experiment_id,
                "total_batches": result.total_batches,
                "batches_successful": result.batches_successful,
                "batches_failed": result.batches_failed,
                "questions_generated": result.questions_generated,
                "questions_valid": result.questions_valid,
                "tokens_used": result.tokens_used,
                "cost_usd": result.cost_usd,
                "output_json": result.output_json_path,
            },
            error_message=result.error_message,
        )

    def _run_validation(
        self,
        request: RunPipelineRequest,
        document_id: str,
    ) -> PipelineStageResult:
        """Ejecuta la etapa de validación."""
        stage_start = datetime.now()

        validate_request = ValidateQuestionsRequest(
            document_id=document_id,
            validation_level=request.validation_level,
            auto_fix=request.auto_fix,
        )

        result = self._validate.execute(validate_request)
        stage_time = (datetime.now() - stage_start).total_seconds()

        return PipelineStageResult(
            stage_name="validate",
            success=result.success,
            execution_time_seconds=stage_time,
            details={
                "total_questions": result.total_questions,
                "valid_questions": result.valid_questions,
                "invalid_questions": result.invalid_questions,
                "fixed_questions": result.fixed_questions,
                "issues_by_type": result.issues_by_type,
                "output_invalid": result.output_invalid_path,
            },
            error_message=result.error_message,
        )

    def _get_stage_detail(
        self,
        stages: List[PipelineStageResult],
        stage_name: str,
        key: str,
        default,
    ):
        """Obtiene un detalle de una etapa específica."""
        for stage in stages:
            if stage.stage_name == stage_name:
                return stage.details.get(key, default)
        return default

    def _build_error_result(
        self,
        stages: List[PipelineStageResult],
        start_time: datetime,
        error_message: str,
    ) -> RunPipelineResult:
        """Construye resultado de error."""
        return RunPipelineResult(
            success=False,
            stages=stages,
            total_execution_time_seconds=(datetime.now() - start_time).total_seconds(),
            error_message=error_message,
        )