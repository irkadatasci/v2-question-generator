"""
PyMuPDF Extractor - Extractor de secciones usando PyMuPDF.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ...domain.entities.document import Document
from ...domain.entities.section import Section
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class PyMuPDFExtractionConfig:
    """Configuración para extracción de PDF con PyMuPDF."""
    min_section_length: int = 50
    merge_short_sections: bool = True
    extract_tables: bool = True
    extract_images: bool = False


class PyMuPDFExtractor:
    """
    Extractor de secciones usando PyMuPDF (fitz).
    
    Utiliza PyMuPDF para extraer texto básico de documentos PDF,
    segmentando por páginas y creando secciones simples.
    """

    def __init__(self, config: Optional[PyMuPDFExtractionConfig] = None):
        """
        Args:
            config: Configuración de extracción
        """
        self._config = config or PyMuPDFExtractionConfig()

    def extract(self, pdf_path: Path) -> Tuple[Document, List[Section]]:
        """
        Extrae secciones de un PDF usando PyMuPDF.

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
        
        doc = None  # Inicializar variable

        try:
            import fitz  # PyMuPDF
            
            # Abrir PDF
            doc = fitz.open(pdf_path)
            
            # Extraer secciones por página
            sections = []
            section_id = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extraer texto de la página
                text = page.get_text()
                
                if len(text.strip()) < self._config.min_section_length:
                    continue
                
                # Crear sección para esta página
                title = f"Página {page_num + 1}"
                
                # Crear coordenadas por defecto (sin el parámetro page)
                coordinates = Coordinates(
                    x=0, y=0, width=0, height=0
                )
                
                section = Section(
                    id=section_id,
                    document_id=document.id,
                    title=title,
                    page=page_num + 1,
                    text=text.strip(),
                    coordinates=coordinates,
                )
                
                sections.append(section)
                section_id += 1

            # Actualizar documento con información
            document.total_pages = len(doc)
            document.mark_as_processed()

            # Merge secciones cortas si está configurado
            if self._config.merge_short_sections:
                sections = self._merge_short_sections(sections)

            return document, sections

        except ImportError:
            raise ImportError(
                "Se requiere PyMuPDF (fitz): "
                "pip install PyMuPDF"
            )
        except Exception as e:
            raise Exception(f"Error procesando PDF con PyMuPDF: {e}")
        finally:
            # Cerrar documento en cualquier caso
            if doc is not None:
                doc.close()

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