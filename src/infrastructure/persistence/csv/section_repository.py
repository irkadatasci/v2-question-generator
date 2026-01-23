"""
Section Repository CSV - Repositorio de secciones en CSV.
"""

import csv
import glob
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ....application.ports.repositories import SectionRepository
from ....domain.entities.section import Section, SectionStatus
from ....domain.value_objects.coordinates import Coordinates
from ....domain.value_objects.classification import Classification, ClassificationResult


class SectionRepositoryCSV(SectionRepository):
    """
    Repositorio de secciones usando CSV como almacenamiento.

    Formato CSV compatible con el sistema actual para facilitar migración.
    """

    # Columnas del CSV
    COLUMNS = [
        "id",
        "document_id",
        "title",
        "page",
        "text",
        "text_length",
        "coord_x",
        "coord_y",
        "coord_width",
        "coord_height",
        "status",
        "classification",
        "classification_score",
        "semantic_autonomy",
        "legal_relevance",
        "concept_density",
        "context_coherence",
    ]

    def __init__(self, base_path: Path):
        """
        Args:
            base_path: Ruta base para almacenar archivos CSV
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

        # Cache en memoria por documento
        self._cache: dict[str, List[Section]] = {}

    def save(self, section: Section) -> None:
        """Guarda una sección."""
        sections = self._cache.get(section.document_id, [])

        # Buscar si ya existe
        existing_idx = None
        for i, s in enumerate(sections):
            if s.id == section.id:
                existing_idx = i
                break

        if existing_idx is not None:
            sections[existing_idx] = section
        else:
            sections.append(section)

        self._cache[section.document_id] = sections

    def save_all(self, sections: List[Section]) -> None:
        """Guarda múltiples secciones."""
        for section in sections:
            self.save(section)

    def find_by_id(self, section_id: int, document_id: str) -> Optional[Section]:
        """Busca una sección por ID."""
        sections = self._cache.get(document_id, [])
        for section in sections:
            if section.id == section_id:
                return section
        return None

    def find_all(self, document_id: str) -> List[Section]:
        """Retorna todas las secciones de un documento."""
        return self._cache.get(document_id, [])

    def find_by_classification(
        self,
        document_id: str,
        classification: Classification,
    ) -> List[Section]:
        """Busca secciones por clasificación."""
        sections = self._cache.get(document_id, [])
        return [
            s for s in sections
            if s.classification and s.classification.classification == classification
        ]

    def find_relevant(self, document_id: str) -> List[Section]:
        """Retorna secciones relevantes de un documento."""
        sections = self._cache.get(document_id, [])
        relevant_classifications = {
            Classification.RELEVANT,
            Classification.AUTO_CONSERVED,
            Classification.REVIEW_NEEDED,
        }

        return [
            s for s in sections
            if s.classification and s.classification.classification in relevant_classifications
        ]

    def find_by_page(self, document_id: str, page: int) -> List[Section]:
        """Busca secciones por número de página."""
        sections = self._cache.get(document_id, [])
        return [s for s in sections if s.page == page]

    def count(self, document_id: str) -> int:
        """Cuenta secciones de un documento."""
        return len(self._cache.get(document_id, []))

    def count_by_classification(self, document_id: str) -> dict:
        """Cuenta secciones agrupadas por clasificación."""
        sections = self._cache.get(document_id, [])
        counts = Counter(
            s.classification.classification.value
            for s in sections if s.classification
        )
        return dict(counts)

    def delete(self, section_id: int, document_id: str) -> bool:
        """Elimina una sección."""
        sections = self._cache.get(document_id, [])
        original_len = len(sections)

        sections = [s for s in sections if s.id != section_id]
        self._cache[document_id] = sections

        return len(sections) < original_len

    def delete_all(self, document_id: str) -> int:
        """Elimina todas las secciones de un documento."""
        if document_id in self._cache:
            count = len(self._cache[document_id])
            del self._cache[document_id]
            return count
        return 0

    def export_to_csv(
        self,
        document_id: str,
        output_path: Path,
    ) -> Path:
        """
        Exporta secciones a CSV.

        Args:
            document_id: ID del documento
            output_path: Ruta de salida (directorio)

        Returns:
            Ruta del archivo CSV generado
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = output_path / f"secciones_{document_id}_{timestamp}.csv"

        sections = self._cache.get(document_id, [])

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNS, delimiter=";")
            writer.writeheader()

            for section in sections:
                row = self._section_to_row(section)
                writer.writerow(row)

        return csv_file

    def load_from_csv(self, csv_path: Path, document_id: str) -> List[Section]:
        """
        Importa secciones desde CSV.

        Args:
            csv_path: Ruta del archivo CSV
            document_id: ID del documento a asociar

        Returns:
            Lista de secciones importadas
        """
        sections = []

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")

            for row in reader:
                section = self._row_to_section(row)
                # Forzar el document_id
                section.document_id = document_id
                sections.append(section)

        # Guardar en cache
        if sections:
            self._cache[document_id] = sections

        return sections

    def get_latest_csv(self, pattern: str = "secciones_*.csv") -> Optional[Path]:
        """
        Obtiene el CSV más reciente que coincide con el patrón en el base_path.

        Args:
            pattern: Patrón glob para buscar archivos

        Returns:
            Ruta del archivo más reciente o None
        """
        files = glob.glob(str(self._base_path / pattern))
        if not files:
            return None
        
        latest_file = max(files, key=lambda f: Path(f).stat().st_mtime)
        return Path(latest_file)

    def _section_to_row(self, section: Section) -> dict:
        """Convierte una sección a fila CSV."""
        row = {
            "id": section.id,
            "document_id": section.document_id,
            "title": section.title,
            "page": section.page,
            "text": section.text,
            "text_length": section.text_length,
            "coord_x": section.coordinates.x,
            "coord_y": section.coordinates.y,
            "coord_width": section.coordinates.width,
            "coord_height": section.coordinates.height,
            "status": section.status.value,
            "classification": "",
            "classification_score": 0,
            "semantic_autonomy": 0,
            "legal_relevance": 0,
            "concept_density": 0,
            "context_coherence": 0,
        }

        if section.classification and section.classification.metrics:
            row["classification"] = section.classification.classification.value
            row["classification_score"] = section.classification.score
            metrics = section.classification.metrics
            row["semantic_autonomy"] = metrics.semantic_autonomy
            row["legal_relevance"] = metrics.legal_relevance
            row["concept_density"] = metrics.concept_density
            row["context_coherence"] = metrics.context_coherence

        return row

    def _safe_float(self, value, default=0.0):
        """Convierte a float de manera segura, manejando None y valores inválidos."""
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value, default=0):
        """Convierte a int de manera segura, manejando None y valores inválidos."""
        if value is None or value == "":
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _row_to_section(self, row: dict) -> Section:
        """Convierte una fila CSV a sección."""
        coordinates = Coordinates(
            x=self._safe_float(row.get("coord_x", 0)),
            y=self._safe_float(row.get("coord_y", 0)),
            width=self._safe_float(row.get("coord_width", 0)),
            height=self._safe_float(row.get("coord_height", 0)),
        )

        classification = None
        if row.get("classification") and row.get("classification").strip():
            from ....domain.value_objects.classification import ClassificationMetrics
            
            # Crear métricas si existen
            metrics = None
            if row.get("semantic_autonomy") is not None and str(row.get("semantic_autonomy")).strip():
                metrics = ClassificationMetrics(
                    semantic_autonomy=self._safe_float(row.get("semantic_autonomy", 0)),
                    legal_relevance=self._safe_float(row.get("legal_relevance", 0)),
                    concept_density=self._safe_float(row.get("concept_density", 0)),
                    context_coherence=self._safe_float(row.get("context_coherence", 0)),
                )
            
            classification = ClassificationResult(
                classification=Classification(row["classification"]),
                score=self._safe_float(row.get("classification_score", 0)),
                metrics=metrics,
            )

        return Section(
            id=self._safe_int(row.get("id", 0)),
            document_id=row.get("document_id", ""),
            title=row.get("title", ""),
            page=self._safe_int(row.get("page", 1)),
            text=row.get("text", ""),
            coordinates=coordinates,
            status=SectionStatus(row.get("status", "pending")),
            classification=classification,
        )

    def clear_cache(self, document_id: Optional[str] = None) -> None:
        """Limpia el cache."""
        if document_id:
            self._cache.pop(document_id, None)
        else:
            self._cache.clear()