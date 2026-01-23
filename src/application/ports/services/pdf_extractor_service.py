"""
PDF Extractor Service Interface - Contrato para extractores de PDF.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ....domain.entities.section import Section
from ....domain.entities.document import Document


class PDFExtractorService(ABC):
    """
    Interface abstracta para servicios de extracción de PDF.

    Define el contrato que deben implementar los extractores de PDF
    (SpaCy Layout, PyMuPDF, etc.).
    """

    @property
    @abstractmethod
    def extractor_name(self) -> str:
        """Nombre del extractor (spacy-layout, pymupdf, etc.)."""
        pass

    @abstractmethod
    def extract(self, pdf_path: Path) -> tuple[Document, List[Section]]:
        """
        Extrae secciones de un PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (Document, Lista de Sections extraídas)

        Raises:
            FileNotFoundError: Si el PDF no existe
            ExtractionError: Si hay error en la extracción
        """
        pass

    @abstractmethod
    def get_page_count(self, pdf_path: Path) -> int:
        """
        Obtiene el número de páginas del PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Número de páginas
        """
        pass

    @abstractmethod
    def extract_page(self, pdf_path: Path, page_number: int) -> List[Section]:
        """
        Extrae secciones de una página específica.

        Args:
            pdf_path: Ruta al archivo PDF
            page_number: Número de página (1-indexed)

        Returns:
            Lista de Sections de esa página
        """
        pass

    @abstractmethod
    def extract_text_only(self, pdf_path: Path) -> str:
        """
        Extrae solo el texto del PDF (sin estructura).

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Texto completo del PDF
        """
        pass

    @abstractmethod
    def get_pdf_metadata(self, pdf_path: Path) -> dict:
        """
        Obtiene metadata del PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Diccionario con metadata (título, autor, etc.)
        """
        pass

    @abstractmethod
    def validate_pdf(self, pdf_path: Path) -> tuple[bool, str]:
        """
        Valida que el PDF sea procesable.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (es_válido, mensaje)
        """
        pass
