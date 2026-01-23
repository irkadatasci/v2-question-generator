"""
Extract Sections Use Case - Extrae secciones de un PDF.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...domain.entities.document import Document
from ...domain.entities.section import Section
from ..ports.services import PDFExtractorService
from ..ports.repositories import DocumentRepository, SectionRepository


@dataclass
class ExtractSectionsRequest:
    """Request para extraer secciones."""
    pdf_path: Path
    output_dir: Optional[Path] = None
    save_to_csv: bool = True


@dataclass
class ExtractSectionsResult:
    """Resultado de la extracción."""
    success: bool
    document: Optional[Document] = None
    sections: List[Section] = field(default_factory=list)
    total_pages: int = 0
    total_sections: int = 0
    output_csv_path: Optional[Path] = None
    error_message: str = ""
    execution_time_seconds: float = 0.0


class ExtractSectionsUseCase:
    """
    Caso de uso: Extraer secciones de un PDF.

    Orquesta la extracción de secciones desde un documento PDF,
    preservando estructura, jerarquía y coordenadas.

    Etapa 1 del pipeline.
    """

    def __init__(
        self,
        pdf_extractor: PDFExtractorService,
        document_repository: DocumentRepository,
        section_repository: SectionRepository,
    ):
        """
        Args:
            pdf_extractor: Servicio de extracción de PDF
            document_repository: Repositorio de documentos
            section_repository: Repositorio de secciones
        """
        self._pdf_extractor = pdf_extractor
        self._document_repository = document_repository
        self._section_repository = section_repository

    def execute(self, request: ExtractSectionsRequest) -> ExtractSectionsResult:
        """
        Ejecuta la extracción de secciones.

        Args:
            request: Request con parámetros de extracción

        Returns:
            ExtractSectionsResult con el resultado
        """
        start_time = datetime.now()

        try:
            # 1. Validar que el PDF existe y es válido
            is_valid, validation_message = self._pdf_extractor.validate_pdf(request.pdf_path)
            if not is_valid:
                return ExtractSectionsResult(
                    success=False,
                    error_message=f"PDF inválido: {validation_message}",
                )

            # 2. Verificar si ya fue procesado (por hash)
            document = Document.from_path(request.pdf_path)
            existing = self._document_repository.find_by_hash(document.hash)

            if existing:
                # Cargar secciones existentes desde cache primero
                sections = self._section_repository.find_all(existing.id)
                
                # Si no hay secciones en cache, cargar desde CSV
                if not sections:
                    print("📥 Cargando secciones desde CSV...")
                    sections = self._load_sections_from_csv(existing.id)
                    if sections:
                        # Guardar en cache para futuros usos
                        self._section_repository.save_all(sections)
                        print(f"✓ Cargadas {len(sections)} secciones desde CSV")
                
                return ExtractSectionsResult(
                    success=True,
                    document=existing,
                    sections=sections,
                    total_pages=existing.total_pages,
                    total_sections=len(sections),
                    error_message="Documento ya procesado (cargado desde caché)",
                    execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                )

            # 3. Extraer secciones
            document, sections = self._pdf_extractor.extract(request.pdf_path)

            # 4. Guardar documento y secciones
            self._document_repository.save(document)
            self._section_repository.save_all(sections)

            # 5. Exportar a CSV si se requiere
            output_csv = None
            if request.save_to_csv:
                output_dir = request.output_dir or Path("datos/intermediate/preprocesamiento")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_csv = self._section_repository.export_to_csv(
                    document_id=document.id,
                    output_path=output_dir,
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return ExtractSectionsResult(
                success=True,
                document=document,
                sections=sections,
                total_pages=document.total_pages,
                total_sections=len(sections),
                output_csv_path=output_csv,
                execution_time_seconds=execution_time,
            )

        except FileNotFoundError as e:
            return ExtractSectionsResult(
                success=False,
                error_message=f"Archivo no encontrado: {e}",
            )
        except Exception as e:
            return ExtractSectionsResult(
                success=False,
                error_message=f"Error en extracción: {e}",
            )

    def _load_sections_from_csv(self, document_id: str) -> List[Section]:
        """
        Carga secciones desde CSV para un documento específico.
        
        Args:
            document_id: ID del documento
            
        Returns:
            Lista de secciones cargadas
        """
        try:
            # Buscar el CSV más reciente para este documento
            sections_dir = Path("datos/intermediate/preprocesamiento")
            pattern = f"secciones_{document_id}*.csv"
            
            import glob
            files = glob.glob(str(sections_dir / pattern))
            if not files:
                print(f"❌ No se encontró archivo CSV para documento {document_id}")
                return []
            
            # Obtener el archivo más reciente
            latest_file = max(files, key=lambda f: Path(f).stat().st_mtime)
            
            # Cargar desde CSV
            return self._section_repository.load_from_csv(Path(latest_file), document_id)
            
        except Exception as e:
            print(f"❌ Error cargando secciones desde CSV: {e}")
            return []