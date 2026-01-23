"""
Classification Service Interface - Contrato para clasificadores semánticos.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from ....domain.entities.section import Section
from ....domain.value_objects.classification import ClassificationResult, ClassificationMetrics


class ClassificationService(ABC):
    """
    Interface abstracta para servicios de clasificación semántica.

    Define el contrato que deben implementar los clasificadores
    de secciones (basado en reglas, ML, etc.).
    """

    @property
    @abstractmethod
    def classifier_name(self) -> str:
        """Nombre del clasificador (semantic-rules, ml-based, etc.)."""
        pass

    @abstractmethod
    def classify(self, section: Section) -> ClassificationResult:
        """
        Clasifica una sección.

        Args:
            section: Sección a clasificar

        Returns:
            Resultado de clasificación
        """
        pass

    @abstractmethod
    def classify_batch(self, sections: List[Section]) -> List[ClassificationResult]:
        """
        Clasifica múltiples secciones.

        Args:
            sections: Lista de secciones a clasificar

        Returns:
            Lista de resultados de clasificación
        """
        pass

    @abstractmethod
    def calculate_metrics(self, text: str) -> ClassificationMetrics:
        """
        Calcula métricas de clasificación para un texto.

        Args:
            text: Texto a evaluar

        Returns:
            Métricas de clasificación
        """
        pass

    @abstractmethod
    def get_weights(self) -> Dict[str, float]:
        """
        Obtiene los pesos actuales de las métricas.

        Returns:
            Diccionario con pesos {metrica: peso}
        """
        pass

    @abstractmethod
    def set_weights(
        self,
        semantic_autonomy: float = 0.30,
        legal_relevance: float = 0.40,
        concept_density: float = 0.20,
        context_coherence: float = 0.10,
    ) -> None:
        """
        Configura los pesos de las métricas.

        Args:
            semantic_autonomy: Peso de autonomía semántica
            legal_relevance: Peso de relevancia jurídica
            concept_density: Peso de densidad de conceptos
            context_coherence: Peso de coherencia
        """
        pass

    @abstractmethod
    def get_thresholds(self) -> Dict[str, float]:
        """
        Obtiene los umbrales actuales.

        Returns:
            Diccionario con umbrales
        """
        pass

    @abstractmethod
    def set_thresholds(
        self,
        relevant: float = 0.7,
        review: float = 0.5,
        auto_conserve_length: int = 300,
    ) -> None:
        """
        Configura los umbrales de clasificación.

        Args:
            relevant: Umbral para RELEVANTE
            review: Umbral para REVISION_MANUAL
            auto_conserve_length: Longitud mínima para AUTO_CONSERVADA
        """
        pass

    @abstractmethod
    def get_statistics(self, results: List[ClassificationResult]) -> Dict:
        """
        Obtiene estadísticas de clasificación.

        Args:
            results: Lista de resultados

        Returns:
            Diccionario con estadísticas
        """
        pass

    @abstractmethod
    def add_domain_terms(self, terms: Dict[str, float]) -> None:
        """
        Agrega términos del dominio para relevancia.

        Args:
            terms: Diccionario {término: peso}
        """
        pass

    @abstractmethod
    def get_domain_terms(self) -> Dict[str, float]:
        """
        Obtiene los términos del dominio configurados.

        Returns:
            Diccionario con términos y pesos
        """
        pass
