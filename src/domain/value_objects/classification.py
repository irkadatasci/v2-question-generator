"""
Classification Value Objects - Clasificación semántica de secciones.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class Classification(Enum):
    """Clasificación de relevancia de una sección."""
    RELEVANT = "RELEVANTE"
    DISCARDABLE = "DESCARTABLE"
    REVIEW_NEEDED = "REVISION_MANUAL"
    AUTO_CONSERVED = "AUTO_CONSERVADA"


@dataclass(frozen=True)
class ClassificationMetrics:
    """
    Métricas individuales de clasificación semántica.

    Cada métrica contribuye al score integral con su peso correspondiente:
    - Autonomía Semántica (30%): ¿Puede entenderse sin contexto?
    - Relevancia Jurídica (40%): ¿Contiene términos jurídicos importantes?
    - Densidad de Conceptos (20%): ¿Cuántos conceptos por 100 caracteres?
    - Contexto Coherencia (10%): ¿Es completo y coherente?

    Attributes:
        semantic_autonomy: Puntuación de autonomía semántica (0-100)
        legal_relevance: Puntuación de relevancia jurídica (0-100)
        concept_density: Puntuación de densidad de conceptos (0-100)
        context_coherence: Puntuación de coherencia (0-100)
    """

    semantic_autonomy: float  # AS - 30%
    legal_relevance: float    # RJ - 40%
    concept_density: float    # DC - 20%
    context_coherence: float  # CC - 10%

    def __post_init__(self) -> None:
        """Valida que las métricas estén en rango válido."""
        for metric_name, metric_value in [
            ("semantic_autonomy", self.semantic_autonomy),
            ("legal_relevance", self.legal_relevance),
            ("concept_density", self.concept_density),
            ("context_coherence", self.context_coherence),
        ]:
            if not 0 <= metric_value <= 100:
                raise ValueError(f"{metric_name} debe estar entre 0 y 100, recibido: {metric_value}")

    def calculate_score(
        self,
        weight_as: float = 0.30,
        weight_rj: float = 0.40,
        weight_dc: float = 0.20,
        weight_cc: float = 0.10,
    ) -> float:
        """
        Calcula el score integral ponderado.

        Formula: S = (AS × w_as) + (RJ × w_rj) + (DC × w_dc) + (CC × w_cc)

        Args:
            weight_as: Peso de autonomía semántica (default 0.30)
            weight_rj: Peso de relevancia jurídica (default 0.40)
            weight_dc: Peso de densidad de conceptos (default 0.20)
            weight_cc: Peso de coherencia (default 0.10)

        Returns:
            Score integral normalizado (0.0 - 1.0)
        """
        # Normalizar métricas a 0-1
        as_norm = self.semantic_autonomy / 100
        rj_norm = self.legal_relevance / 100
        dc_norm = self.concept_density / 100
        cc_norm = self.context_coherence / 100

        # Calcular score ponderado
        score = (
            as_norm * weight_as
            + rj_norm * weight_rj
            + dc_norm * weight_dc
            + cc_norm * weight_cc
        )

        return round(score, 4)

    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        return {
            "autonomia_semantica": self.semantic_autonomy,
            "relevancia_juridica": self.legal_relevance,
            "densidad_conceptos": self.concept_density,
            "contexto_coherencia": self.context_coherence,
        }


@dataclass(frozen=True)
class ClassificationResult:
    """
    Resultado completo de clasificación de una sección.

    Attributes:
        classification: Clasificación final
        score: Score integral (0.0 - 1.0)
        metrics: Métricas individuales (opcional)
        reason: Razón de la clasificación
    """

    classification: Classification
    score: float
    metrics: Optional[ClassificationMetrics] = None
    reason: str = ""

    def __post_init__(self) -> None:
        """Valida el score."""
        if not 0 <= self.score <= 1:
            raise ValueError(f"Score debe estar entre 0 y 1, recibido: {self.score}")

    @classmethod
    def create(
        cls,
        metrics: ClassificationMetrics,
        text_length: int,
        threshold_relevant: float = 0.7,
        threshold_review: float = 0.5,
        auto_conserve_length: int = 300,
    ) -> "ClassificationResult":
        """
        Factory method que crea un ClassificationResult a partir de métricas.

        Aplica la lógica de clasificación:
        - Si longitud >= auto_conserve_length → AUTO_CONSERVADA
        - Si score >= threshold_relevant → RELEVANTE
        - Si score >= threshold_review → REVISION_MANUAL
        - Si no → DESCARTABLE

        Args:
            metrics: Métricas de clasificación
            text_length: Longitud del texto en caracteres
            threshold_relevant: Umbral para RELEVANTE (default 0.7)
            threshold_review: Umbral para REVISION_MANUAL (default 0.5)
            auto_conserve_length: Longitud mínima para auto-conservar (default 300)

        Returns:
            Nueva instancia de ClassificationResult
        """
        score = metrics.calculate_score()

        # Lógica de clasificación
        if text_length >= auto_conserve_length:
            classification = Classification.AUTO_CONSERVED
            reason = f"Sección larga ({text_length} chars) - conservada automáticamente"
        elif score >= threshold_relevant:
            classification = Classification.RELEVANT
            reason = f"Score alto ({score:.3f} >= {threshold_relevant})"
        elif score >= threshold_review:
            classification = Classification.REVIEW_NEEDED
            reason = f"Score medio ({score:.3f} >= {threshold_review})"
        else:
            classification = Classification.DISCARDABLE
            reason = f"Score bajo ({score:.3f} < {threshold_review})"

        return cls(
            classification=classification,
            score=score,
            metrics=metrics,
            reason=reason,
        )

    @property
    def is_relevant(self) -> bool:
        """Indica si la sección es relevante para procesamiento."""
        return self.classification in (
            Classification.RELEVANT,
            Classification.AUTO_CONSERVED,
            Classification.REVIEW_NEEDED,
        )

    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        return {
            "clasificacion": self.classification.value,
            "score": self.score,
            "metricas": self.metrics.to_dict() if self.metrics else None,
            "razon": self.reason,
        }
