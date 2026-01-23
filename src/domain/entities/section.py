"""
Section Entity - Representa una sección extraída de un documento.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from ..value_objects.coordinates import Coordinates
from ..value_objects.classification import Classification, ClassificationResult


class SectionStatus(Enum):
    """Estado de procesamiento de una sección."""
    PENDING = "pending"
    CLASSIFIED = "classified"
    PROCESSED = "processed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class Section:
    """
    Entidad que representa una sección extraída de un documento PDF.

    Una sección es un bloque de texto con estructura semántica propia,
    identificado por un título y coordenadas en el documento original.

    Attributes:
        id: Identificador único de la sección (correlativo)
        document_id: ID del documento padre
        title: Título de la sección (puede incluir jerarquía)
        original_title: Título original sin jerarquía
        page: Número de página donde inicia
        text: Contenido textual completo
        coordinates: Coordenadas en el PDF
        text_length: Longitud del texto en caracteres
        status: Estado de procesamiento
        classification: Resultado de clasificación semántica
    """

    id: int
    document_id: str
    title: str
    page: int
    text: str
    coordinates: Coordinates
    text_length: int = field(init=False)
    original_title: Optional[str] = None
    status: SectionStatus = SectionStatus.PENDING
    classification: Optional[ClassificationResult] = None

    def __post_init__(self) -> None:
        """Calcula campos derivados después de la inicialización."""
        self.text_length = len(self.text)
        if self.original_title is None:
            self.original_title = self.title

    def classify(self, result: ClassificationResult) -> None:
        """
        Aplica resultado de clasificación a la sección.

        Args:
            result: Resultado de clasificación semántica
        """
        self.classification = result
        self.status = SectionStatus.CLASSIFIED

    def mark_as_processed(self) -> None:
        """Marca la sección como procesada."""
        self.status = SectionStatus.PROCESSED

    def mark_as_skipped(self, reason: str = "") -> None:
        """Marca la sección como saltada."""
        self.status = SectionStatus.SKIPPED

    def mark_as_error(self, error: str = "") -> None:
        """Marca la sección con error."""
        self.status = SectionStatus.ERROR

    @property
    def is_relevant(self) -> bool:
        """Indica si la sección es relevante para generación de preguntas."""
        if self.classification is None:
            return True  # Por defecto, sin clasificación se considera relevante
        return self.classification.classification in (
            Classification.RELEVANT,
            Classification.AUTO_CONSERVED,
            Classification.REVIEW_NEEDED,
        )

    @property
    def is_long(self) -> bool:
        """Indica si es una sección larga (>300 chars por defecto)."""
        return self.text_length >= 300

    def to_csv_row(self) -> dict:
        """Convierte la sección a formato de fila CSV."""
        return {
            "ID_Seccion": self.id,
            "Titulo": self.title,
            "Pagina": self.page,
            "Longitud_Texto": self.text_length,
            "Coordenadas_X": self.coordinates.x,
            "Coordenadas_Y": self.coordinates.y,
            "Ancho": self.coordinates.width,
            "Alto": self.coordinates.height,
            "Texto_Completo": self.text,
            "Clasificacion": self.classification.classification.value if self.classification else "",
            "Score": self.classification.score if self.classification else 0.0,
        }

    def __hash__(self) -> int:
        return hash((self.document_id, self.id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Section):
            return False
        return self.document_id == other.document_id and self.id == other.id
