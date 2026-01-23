"""
Classify Sections Use Case - Clasifica secciones semánticamente.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ...domain.entities.section import Section
from ...domain.value_objects.classification import Classification, ClassificationResult
from ..ports.services import ClassificationService
from ..ports.repositories import SectionRepository


@dataclass
class ClassifySectionsRequest:
    """Request para clasificar secciones."""
    document_id: str
    threshold_relevant: float = 0.7
    threshold_review: float = 0.5
    auto_conserve_length: int = 300
    save_results: bool = True


@dataclass
class ClassifySectionsResult:
    """Resultado de la clasificación."""
    success: bool
    sections_classified: int = 0
    classification_counts: Dict[str, int] = field(default_factory=dict)
    average_score: float = 0.0
    sections_relevant: int = 0
    sections_discarded: int = 0
    output_csv_path: Optional[Path] = None
    error_message: str = ""
    execution_time_seconds: float = 0.0


class ClassifySectionsUseCase:
    """
    Caso de uso: Clasificar secciones semánticamente.

    Evalúa cada sección con 4 métricas y asigna clasificación
    (RELEVANTE, REVISION_MANUAL, DESCARTABLE, AUTO_CONSERVADA).

    Etapa 2 del pipeline.
    """

    def __init__(
        self,
        classification_service: ClassificationService,
        section_repository: SectionRepository,
    ):
        """
        Args:
            classification_service: Servicio de clasificación
            section_repository: Repositorio de secciones
        """
        self._classification_service = classification_service
        self._section_repository = section_repository

    def execute(self, request: ClassifySectionsRequest) -> ClassifySectionsResult:
        """
        Ejecuta la clasificación de secciones.

        Args:
            request: Request con parámetros de clasificación

        Returns:
            ClassifySectionsResult con el resultado
        """
        start_time = datetime.now()

        try:
            # 1. Configurar umbrales
            self._classification_service.set_thresholds(
                relevant=request.threshold_relevant,
                review=request.threshold_review,
                auto_conserve_length=request.auto_conserve_length,
            )

            # 2. Obtener secciones del documento
            sections = self._section_repository.find_all(request.document_id)

            if not sections:
                return ClassifySectionsResult(
                    success=False,
                    error_message=f"No se encontraron secciones para documento {request.document_id}",
                )

            # 3. Clasificar todas las secciones
            results = self._classification_service.classify_batch(sections)

            # 4. Aplicar resultados a las secciones
            classification_counts = {c.value: 0 for c in Classification}
            total_score = 0.0

            for section, result in zip(sections, results):
                section.classify(result)
                classification_counts[result.classification.value] += 1
                total_score += result.score

            # 5. Guardar secciones actualizadas
            if request.save_results:
                self._section_repository.save_all(sections)

            # 6. Calcular estadísticas
            average_score = total_score / len(sections) if sections else 0.0

            relevant_count = (
                classification_counts.get(Classification.RELEVANT.value, 0)
                + classification_counts.get(Classification.AUTO_CONSERVED.value, 0)
                + classification_counts.get(Classification.REVIEW_NEEDED.value, 0)
            )
            discarded_count = classification_counts.get(Classification.DISCARDABLE.value, 0)

            # 7. Exportar a CSV si hay secciones
            output_csv = None
            if request.save_results:
                output_csv = self._section_repository.export_to_csv(
                    document_id=request.document_id,
                    output_path=Path("datos/intermediate/preprocesamiento"),
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return ClassifySectionsResult(
                success=True,
                sections_classified=len(sections),
                classification_counts=classification_counts,
                average_score=round(average_score, 4),
                sections_relevant=relevant_count,
                sections_discarded=discarded_count,
                output_csv_path=output_csv,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            return ClassifySectionsResult(
                success=False,
                error_message=f"Error en clasificación: {e}",
            )
