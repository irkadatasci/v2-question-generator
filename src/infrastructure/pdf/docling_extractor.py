"""
Docling Extractor - Extractor de secciones usando docling.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ...domain.entities.document import Document
from ...domain.entities.section import Section
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class DoclingExtractionConfig:
    """Configuración para extracción de PDF con docling."""
    min_section_length: int = 50
    merge_short_sections: bool = True
    extract_tables: bool = True
    extract_images: bool = False


class DoclingExtractor:
    """
    Extractor de secciones usando docling.
    
    Utiliza docling para extraer secciones estructuradas
    de documentos PDF, preservando jerarquía y coordenadas.
    """

    def __init__(self, config: Optional[DoclingExtractionConfig] = None):
        """
        Args:
            config: Configuración de extracción
        """
        self._config = config or DoclingExtractionConfig()

    def extract(self, pdf_path: Path) -> Tuple[Document, List[Section]]:
        """
        Extrae secciones de un PDF usando docling.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Tupla (Document, List[Section])
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        # Crear documento
        document = Document.from_path(pdf_path)

        try:
            # Importar docling
            from docling.document import Document as DoclingDocument
            from docling.pipeline.standard_pipeline import StandardPdfPipeline
            from docling.datamodel.base_models import InputFormat
            
            # Configurar pipeline
            pipeline = StandardPdfPipeline()
            
            # Procesar documento
            result = pipeline.process(input_source=str(pdf_path))
            docling_doc = result.document
            
            # Extraer secciones del documento docling
            sections = []
            section_id = 0
            
            # Obtener todas las secciones del documento
            for section_data in docling_doc.texts:
                # Obtener texto de la sección
                text = section_data.text.strip()
                
                if len(text) < self._config.min_section_length:
                    continue
                
                # Extraer página
                page = section_data.page_no if hasattr(section_data, 'page_no') else 1
                
                # Extraer título (primera línea)
                title = self._extract_title(text)
                
                # Crear coordenadas por defecto
                coordinates = Coordinates(x=0, y=0, width=0, height=0, page=page)
                
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

            # Obtener total de páginas
            document.total_pages = self._get_total_pages(docling_doc)
            document.mark_as_processed()

            # Merge secciones cortas si está configurado
            if self._config.merge_short_sections:
                sections = self._merge_short_sections(sections)

            return document, sections

        except ImportError:
            raise ImportError(
                "Se requiere docling: "
                "pip install docling"
            )
        except Exception as e:
            raise Exception(f"Error procesando PDF con docling: {e}")

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

    def _extract_title(self, text: str) -> str:
        """Extrae título de un texto."""
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 100:
                return first_line
        return ""

    def _get_total_pages(self, docling_doc) -> int:
        """Obtiene total de páginas del documento."""
        try:
            if hasattr(docling_doc, 'pages'):
                return len(docling_doc.pages)
            return 1
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