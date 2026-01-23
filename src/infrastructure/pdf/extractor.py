"""
Spacy Layout Extractor - Extractor de secciones usando spacy-layout.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ...domain.entities.document import Document
from ...domain.entities.section import Section
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class ExtractionConfig:
    """Configuración para extracción de PDF."""
    model_name: str = "en_core_web_sm"
    min_section_length: int = 50
    merge_short_sections: bool = True
    extract_tables: bool = True
    extract_images: bool = False


class SpacyLayoutExtractor:
    """
    Extractor de secciones usando spacy-layout.

    Utiliza spacy-layout para extraer secciones estructuradas
    de documentos PDF, preservando jerarquía y coordenadas.
    """

    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Args:
            config: Configuración de extracción
        """
        self._config = config or ExtractionConfig()
        self._nlp = None
        self._layout = None

    def _initialize(self) -> None:
        """Inicializa spacy y spacy-layout."""
        if self._nlp is not None:
            return

        try:
            import spacy
            from spacy_layout import spaCyLayout
        except ImportError:
            raise ImportError(
                "Se requiere spacy y spacy-layout: "
                "pip install spacy spacy-layout"
            )

        # Cargar modelo de spacy
        try:
            self._nlp = spacy.load(self._config.model_name)
        except OSError:
            # Descargar modelo si no existe
            import subprocess
            subprocess.run(
                ["python", "-m", "spacy", "download", self._config.model_name],
                check=True
            )
            self._nlp = spacy.load(self._config.model_name)

        # Inicializar spacy-layout
        self._layout = spaCyLayout(self._nlp)

    def extract(self, pdf_path: Path) -> Tuple[Document, List[Section]]:
        """
        Extrae secciones de un PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (Document, List[Section])
        """
        self._initialize()

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        # Crear documento
        document = Document.from_path(pdf_path)

        # Procesar PDF con spacy-layout
        doc = self._layout(pdf_path)

        # Extraer secciones
        sections = []
        section_id = 0

        for span in doc.spans.get("sections", []):
            # Obtener datos del span
            text = span.text.strip()

            if len(text) < self._config.min_section_length:
                continue

            # Extraer coordenadas si disponibles
            coordinates = self._extract_coordinates(span)

            # Extraer página
            page = self._extract_page(span)

            # Extraer título
            title = self._extract_title(span)

            section = Section(
                id=section_id,
                document_id=document.id,
                title=title,
                page=page,
                text=text,
                coordinates=coordinates,
            )

            sections.append(section)
            section_id += 1

        # Actualizar documento con información
        document.total_pages = self._get_total_pages(doc)
        document.mark_as_processed()

        # Merge secciones cortas si está configurado
        if self._config.merge_short_sections:
            sections = self._merge_short_sections(sections)

        return document, sections

    def validate_pdf(self, pdf_path: Path) -> Tuple[bool, str]:
        """
        Valida que el PDF sea procesable.

        Args:
            pdf_path: Ruta al PDF

        Returns:
            Tupla (es_válido, mensaje)
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return False, f"Archivo no existe: {pdf_path}"

        if not pdf_path.suffix.lower() == ".pdf":
            return False, f"No es un archivo PDF: {pdf_path.suffix}"

        # Verificar que se pueda abrir
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            pages = len(doc)
            doc.close()

            if pages == 0:
                return False, "PDF vacío (0 páginas)"

            return True, f"PDF válido ({pages} páginas)"

        except ImportError:
            # Sin PyMuPDF, solo verificar extensión
            return True, "PDF parece válido (no se pudo verificar contenido)"

        except Exception as e:
            return False, f"Error al abrir PDF: {e}"

    def _extract_coordinates(self, span) -> Coordinates:
        """Extrae coordenadas de un span de spacy-layout."""
        try:
            # spacy-layout puede tener layout_* attributes
            if hasattr(span, "layout_x"):
                return Coordinates(
                    x=span.layout_x,
                    y=span.layout_y,
                    width=getattr(span, "layout_width", 0),
                    height=getattr(span, "layout_height", 0),
                    page=getattr(span, "layout_page", 1),
                )
        except AttributeError:
            pass

        return Coordinates(x=0, y=0, width=0, height=0, page=1)

    def _extract_page(self, span) -> int:
        """Extrae número de página de un span."""
        try:
            if hasattr(span, "layout_page"):
                return span.layout_page
            if hasattr(span, "_.layout"):
                return span._.layout.get("page", 1)
        except AttributeError:
            pass

        return 1

    def _extract_title(self, span) -> str:
        """Extrae título de un span."""
        try:
            # Buscar en atributos de layout
            if hasattr(span, "_.layout"):
                layout = span._.layout
                if "heading" in layout:
                    return layout["heading"]

            # Usar primera línea como título
            first_line = span.text.split("\n")[0].strip()
            if len(first_line) < 100:
                return first_line

        except AttributeError:
            pass

        return ""

    def _get_total_pages(self, doc) -> int:
        """Obtiene total de páginas del documento."""
        try:
            if hasattr(doc, "_.layout"):
                return doc._.layout.get("total_pages", 1)

            # Calcular desde spans
            max_page = 1
            for span in doc.spans.get("sections", []):
                page = self._extract_page(span)
                if page > max_page:
                    max_page = page
            return max_page

        except AttributeError:
            return 1

    def _merge_short_sections(
        self,
        sections: List[Section],
        min_length: int = 200,
    ) -> List[Section]:
        """
        Fusiona secciones cortas con las anteriores.

        Args:
            sections: Lista de secciones
            min_length: Longitud mínima para considerar fusión

        Returns:
            Lista de secciones fusionadas
        """
        if not sections:
            return sections

        merged = [sections[0]]

        for section in sections[1:]:
            if section.text_length < min_length and merged:
                # Fusionar con la anterior
                prev = merged[-1]
                merged[-1] = Section(
                    id=prev.id,
                    document_id=prev.document_id,
                    title=prev.title,
                    page=prev.page,
                    text=f"{prev.text}\n\n{section.text}",
                    coordinates=prev.coordinates,
                    status=prev.status,
                    classification=prev.classification,
                )
            else:
                merged.append(section)

        return merged
