"""
PDF Extractor Service Implementation - Implementación del puerto PDFExtractorService.
"""

from pathlib import Path
from typing import List, Tuple

from ...application.ports.services import PDFExtractorService
from ...domain.entities.document import Document
from ...domain.entities.section import Section
from .pymupdf_extractor import PyMuPDFExtractor, PyMuPDFExtractionConfig


class PDFExtractorServiceImpl(PDFExtractorService):
    """
    Implementación concreta del servicio de extracción de PDF.

    Utiliza PyMuPDFExtractor como backend de extracción.
    """

    def __init__(self, config: PyMuPDFExtractionConfig = None):
        """
        Args:
            config: Configuración de extracción
        """
        self._extractor = PyMuPDFExtractor(config)

    @property
    def extractor_name(self) -> str:
        """Nombre del extractor."""
        return "PyMuPDF"

    def extract(self, pdf_path: Path) -> Tuple[Document, List[Section]]:
        """
        Extrae secciones de un PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (Document, List[Section])
        """
        return self._extractor.extract(pdf_path)

    def validate_pdf(self, pdf_path: Path) -> Tuple[bool, str]:
        """
        Valida que el PDF sea procesable.

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Tupla (es_válido, mensaje)
        """
        return self._extractor.validate_pdf(pdf_path)

    def get_page_count(self, pdf_path: Path) -> int:
        """
        Obtiene el número de páginas de un PDF.

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Número de páginas
        """
        try:
            import fitz
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0

    def extract_text_only(self, pdf_path: Path) -> str:
        """
        Extrae solo el texto del PDF sin estructura.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Texto extraído
        """
        try:
            import fitz
            doc = fitz.open(pdf_path)
            text_parts = []

            for page in doc:
                text_parts.append(page.get_text())

            doc.close()
            return "\n\n".join(text_parts)

        except Exception:
            return ""

    def extract_page(self, pdf_path: Path, page_number: int) -> List[Section]:
        """
        Extrae secciones de una página específica.

        Args:
            pdf_path: Ruta al archivo PDF
            page_number: Número de página (1-indexed)

        Returns:
            Lista de Sections de esa página
        """
        try:
            # Extraer todo el documento
            document, all_sections = self.extract(pdf_path)

            # Filtrar por página
            sections_for_page = [
                section for section in all_sections
                if section.page == page_number
            ]

            return sections_for_page

        except Exception:
            return []

    def get_pdf_metadata(self, pdf_path: Path) -> dict:
        """
        Obtiene metadata del PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Diccionario con metadata
        """
        metadata = {
            "title": None,
            "author": None,
            "subject": None,
            "creator": None,
            "pages": 0,
            "file_size": 0,
        }

        try:
            import fitz
            pdf_path = Path(pdf_path)

            if not pdf_path.exists():
                return metadata

            # Obtener tamaño de archivo
            metadata["file_size"] = pdf_path.stat().st_size

            # Abrir PDF
            doc = fitz.open(pdf_path)

            # Obtener número de páginas
            metadata["pages"] = len(doc)

            # Obtener metadata del PDF
            pdf_metadata = doc.metadata or {}
            metadata["title"] = pdf_metadata.get("title")
            metadata["author"] = pdf_metadata.get("author")
            metadata["subject"] = pdf_metadata.get("subject")
            metadata["creator"] = pdf_metadata.get("creator")

            doc.close()

        except Exception:
            pass

        return metadata