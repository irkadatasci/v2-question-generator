"""
Section Repository Interface - Contrato para persistencia de secciones.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ....domain.entities.section import Section
from ....domain.value_objects.classification import Classification


class SectionRepository(ABC):
    """
    Interface abstracta para repositorio de secciones.

    Define el contrato que deben implementar los adaptadores de
    persistencia de secciones (CSV, JSON, Database, etc.).
    """

    @abstractmethod
    def save(self, section: Section) -> None:
        """
        Guarda una sección.

        Args:
            section: Sección a guardar
        """
        pass

    @abstractmethod
    def save_all(self, sections: List[Section]) -> None:
        """
        Guarda múltiples secciones.

        Args:
            sections: Lista de secciones a guardar
        """
        pass

    @abstractmethod
    def find_by_id(self, section_id: int, document_id: str) -> Optional[Section]:
        """
        Busca una sección por ID.

        Args:
            section_id: ID de la sección
            document_id: ID del documento

        Returns:
            Sección encontrada o None
        """
        pass

    @abstractmethod
    def find_all(self, document_id: str) -> List[Section]:
        """
        Obtiene todas las secciones de un documento.

        Args:
            document_id: ID del documento

        Returns:
            Lista de secciones
        """
        pass

    @abstractmethod
    def find_by_classification(
        self,
        document_id: str,
        classification: Classification,
    ) -> List[Section]:
        """
        Busca secciones por clasificación.

        Args:
            document_id: ID del documento
            classification: Clasificación a filtrar

        Returns:
            Lista de secciones con esa clasificación
        """
        pass

    @abstractmethod
    def find_relevant(self, document_id: str) -> List[Section]:
        """
        Obtiene secciones relevantes para procesamiento.

        Incluye: RELEVANTE, AUTO_CONSERVADA, REVISION_MANUAL

        Args:
            document_id: ID del documento

        Returns:
            Lista de secciones relevantes
        """
        pass

    @abstractmethod
    def find_by_page(self, document_id: str, page: int) -> List[Section]:
        """
        Busca secciones por número de página.

        Args:
            document_id: ID del documento
            page: Número de página

        Returns:
            Lista de secciones en esa página
        """
        pass

    @abstractmethod
    def count(self, document_id: str) -> int:
        """
        Cuenta el total de secciones de un documento.

        Args:
            document_id: ID del documento

        Returns:
            Número de secciones
        """
        pass

    @abstractmethod
    def count_by_classification(self, document_id: str) -> dict:
        """
        Cuenta secciones agrupadas por clasificación.

        Args:
            document_id: ID del documento

        Returns:
            Diccionario {clasificacion: count}
        """
        pass

    @abstractmethod
    def delete_all(self, document_id: str) -> int:
        """
        Elimina todas las secciones de un documento.

        Args:
            document_id: ID del documento

        Returns:
            Número de secciones eliminadas
        """
        pass

    @abstractmethod
    def export_to_csv(self, document_id: str, output_path: Path) -> Path:
        """
        Exporta secciones a CSV.

        Args:
            document_id: ID del documento
            output_path: Ruta de salida

        Returns:
            Ruta del archivo generado
        """
        pass

    @abstractmethod
    def load_from_csv(self, csv_path: Path, document_id: str) -> List[Section]:
        """
        Carga secciones desde CSV.

        Args:
            csv_path: Ruta del archivo CSV
            document_id: ID del documento

        Returns:
            Lista de secciones cargadas
        """
        pass

    @abstractmethod
    def get_latest_csv(self, pattern: str = "test_salida_v2_*.csv") -> Optional[Path]:
        """
        Obtiene el CSV más reciente que coincide con el patrón.

        Args:
            pattern: Patrón glob para buscar archivos

        Returns:
            Ruta del archivo más reciente o None
        """
        pass
