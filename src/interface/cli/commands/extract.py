"""
Extract Command - Comando para extraer secciones de PDF.
"""

from pathlib import Path
from typing import Optional

from ....infrastructure.config import Settings
from ....infrastructure.pdf import PDFExtractorServiceImpl
from ....infrastructure.persistence import SectionRepositoryCSV, DocumentRepositoryJSON
from ....application.use_cases import ExtractSectionsUseCase, ExtractSectionsRequest


class ExtractCommand:
    """Comando para extraer secciones de un PDF."""

    def __init__(self, settings: Settings):
        """
        Args:
            settings: Configuración de la aplicación
        """
        self._settings = settings

    def execute(
        self,
        pdf_path: Path,
        output_dir: Optional[Path] = None,
    ) -> int:
        """
        Ejecuta la extracción de secciones.

        Args:
            pdf_path: Ruta al PDF
            output_dir: Directorio de salida

        Returns:
            Código de salida
        """
        print(f"📄 Extrayendo secciones de: {pdf_path}")

        # Verificar que el archivo existe
        if not pdf_path.exists():
            print(f"❌ Archivo no encontrado: {pdf_path}")
            return 1

        # Crear servicios
        pdf_extractor = PDFExtractorServiceImpl()
        section_repo = SectionRepositoryCSV(
            self._settings.paths.intermediate_dir / "sections"
        )
        document_repo = DocumentRepositoryJSON(
            self._settings.paths.intermediate_dir / "documents"
        )

        # Crear caso de uso
        use_case = ExtractSectionsUseCase(
            pdf_extractor=pdf_extractor,
            document_repository=document_repo,
            section_repository=section_repo,
        )

        # Ejecutar
        request = ExtractSectionsRequest(
            pdf_path=pdf_path,
            output_dir=output_dir or self._settings.paths.intermediate_dir,
            save_to_csv=True,
        )

        result = use_case.execute(request)

        if result.success:
            print(f"✅ Extracción completada")
            print(f"   📊 Páginas: {result.total_pages}")
            print(f"   📝 Secciones: {result.total_sections}")
            print(f"   📁 CSV: {result.output_csv_path}")
            print(f"   🆔 Document ID: {result.document.id if result.document else 'N/A'}")
            print(f"   ⏱️  Tiempo: {result.execution_time_seconds:.2f}s")
            return 0
        else:
            print(f"❌ Error: {result.error_message}")
            return 1
