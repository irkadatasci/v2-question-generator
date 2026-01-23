"""
Classify Command - Comando para clasificar secciones.
"""

from ....infrastructure.config import Settings
from ....infrastructure.persistence import SectionRepositoryCSV
from ....application.use_cases import ClassifySectionsUseCase, ClassifySectionsRequest


class ClassifyCommand:
    """Comando para clasificar secciones semánticamente."""

    def __init__(self, settings: Settings):
        """
        Args:
            settings: Configuración de la aplicación
        """
        self._settings = settings

    def execute(
        self,
        document_id: str,
        threshold: float = 0.7,
    ) -> int:
        """
        Ejecuta la clasificación de secciones.

        Args:
            document_id: ID del documento
            threshold: Umbral de relevancia

        Returns:
            Código de salida
        """
        print(f"🔍 Clasificando secciones del documento: {document_id}")

        # Crear repositorio
        section_repo = SectionRepositoryCSV(
            self._settings.paths.intermediate_dir / "sections"
        )

        # Por ahora usamos un clasificador simple basado en reglas
        # TODO: Implementar ClassificationService con el algoritmo de 4 métricas
        from ....application.ports.services import ClassificationService
        from ....domain.entities.section import Section
        from ....domain.value_objects.classification import Classification, ClassificationResult
        from typing import List

        class SimpleClassificationService(ClassificationService):
            """Clasificador simple basado en longitud de texto."""

            def __init__(self, threshold: float = 0.7, review_threshold: float = 0.5):
                self._threshold_relevant = threshold
                self._threshold_review = review_threshold
                self._auto_conserve_length = 300

            def set_thresholds(
                self,
                relevant: float = 0.7,
                review: float = 0.5,
                auto_conserve_length: int = 300,
            ) -> None:
                self._threshold_relevant = relevant
                self._threshold_review = review
                self._auto_conserve_length = auto_conserve_length

            def classify(self, section: Section) -> ClassificationResult:
                # Algoritmo simplificado basado en longitud
                text_length = section.text_length

                if text_length >= self._auto_conserve_length:
                    score = min(1.0, text_length / 1000)
                    if score >= self._threshold_relevant:
                        return ClassificationResult(
                            classification=Classification.RELEVANT,
                            score=score,
                            as_score=score,
                            rj_score=score * 0.8,
                            dc_score=score * 0.7,
                            cc_score=score * 0.9,
                        )
                    elif score >= self._threshold_review:
                        return ClassificationResult(
                            classification=Classification.REVIEW_NEEDED,
                            score=score,
                            as_score=score,
                            rj_score=score * 0.6,
                            dc_score=score * 0.5,
                            cc_score=score * 0.7,
                        )

                if text_length < 100:
                    return ClassificationResult(
                        classification=Classification.DISCARDABLE,
                        score=0.2,
                        as_score=0.2,
                        rj_score=0.1,
                        dc_score=0.1,
                        cc_score=0.3,
                    )

                return ClassificationResult(
                    classification=Classification.AUTO_CONSERVED,
                    score=0.5,
                    as_score=0.5,
                    rj_score=0.4,
                    dc_score=0.5,
                    cc_score=0.6,
                )

            def classify_batch(self, sections: List[Section]) -> List[ClassificationResult]:
                return [self.classify(s) for s in sections]

        classification_service = SimpleClassificationService(threshold)

        # Crear caso de uso
        use_case = ClassifySectionsUseCase(
            classification_service=classification_service,
            section_repository=section_repo,
        )

        # Ejecutar
        request = ClassifySectionsRequest(
            document_id=document_id,
            threshold_relevant=threshold,
            threshold_review=self._settings.classification.threshold_review,
            auto_conserve_length=self._settings.classification.auto_conserve_length,
        )

        result = use_case.execute(request)

        if result.success:
            print(f"✅ Clasificación completada")
            print(f"   📊 Secciones clasificadas: {result.sections_classified}")
            print(f"   ✓ Relevantes: {result.sections_relevant}")
            print(f"   ✗ Descartadas: {result.sections_discarded}")
            print(f"   📈 Score promedio: {result.average_score:.3f}")

            if result.classification_counts:
                print(f"   📋 Desglose:")
                for class_name, count in result.classification_counts.items():
                    print(f"      - {class_name}: {count}")

            print(f"   ⏱️  Tiempo: {result.execution_time_seconds:.2f}s")
            return 0
        else:
            print(f"❌ Error: {result.error_message}")
            return 1
