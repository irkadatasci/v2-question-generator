"""
Batch Entity - Representa un grupo de secciones para procesamiento.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from .section import Section
from .question import Question


class BatchStatus(Enum):
    """Estado de procesamiento de un batch."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Algunas secciones fallaron


@dataclass
class BatchResult:
    """Resultado del procesamiento de un batch."""
    questions_generated: int
    questions_valid: int
    questions_invalid: int
    errors: List[str]
    warnings: List[str]
    tokens_used: int = 0
    cost_usd: float = 0.0
    processing_time_seconds: float = 0.0


@dataclass
class Batch:
    """
    Entidad que representa un grupo de secciones para procesamiento.

    Un batch agrupa N secciones para ser procesadas juntas por el LLM,
    optimizando el uso de tokens y permitiendo context caching.

    Attributes:
        id: Identificador único del batch (número correlativo)
        sections: Lista de secciones en el batch
        status: Estado de procesamiento
        questions: Preguntas generadas
        result: Resultado del procesamiento
        created_at: Fecha de creación
        processed_at: Fecha de procesamiento
        error_message: Mensaje de error (si falló)
    """

    id: int
    sections: List[Section]
    status: BatchStatus = BatchStatus.PENDING
    questions: List[Question] = field(default_factory=list)
    result: Optional[BatchResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @classmethod
    def create(cls, batch_id: int, sections: List[Section]) -> "Batch":
        """
        Factory method para crear un batch.

        Args:
            batch_id: Número del batch
            sections: Lista de secciones a procesar

        Returns:
            Nueva instancia de Batch
        """
        return cls(id=batch_id, sections=sections)

    @property
    def size(self) -> int:
        """Número de secciones en el batch."""
        return len(self.sections)

    @property
    def total_text_length(self) -> int:
        """Longitud total del texto de todas las secciones."""
        return sum(s.text_length for s in self.sections)

    @property
    def section_ids(self) -> List[int]:
        """IDs de las secciones en el batch."""
        return [s.id for s in self.sections]

    @property
    def is_completed(self) -> bool:
        """Indica si el batch fue procesado exitosamente."""
        return self.status == BatchStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Indica si el batch falló."""
        return self.status == BatchStatus.FAILED

    def start_processing(self) -> None:
        """Marca el batch como en procesamiento."""
        self.status = BatchStatus.PROCESSING

    def complete(
        self,
        questions: List[Question],
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        processing_time: float = 0.0,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> None:
        """
        Marca el batch como completado con resultados.

        Args:
            questions: Lista de preguntas generadas
            tokens_used: Tokens usados en la generación
            cost_usd: Costo en USD
            processing_time: Tiempo de procesamiento en segundos
            errors: Lista de errores
            warnings: Lista de advertencias
        """
        self.questions = questions
        self.processed_at = datetime.now()

        valid_questions = [q for q in questions if q.status.value == "validated"]
        invalid_questions = [q for q in questions if q.status.value == "invalid"]

        self.result = BatchResult(
            questions_generated=len(questions),
            questions_valid=len(valid_questions),
            questions_invalid=len(invalid_questions),
            errors=errors or [],
            warnings=warnings or [],
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            processing_time_seconds=processing_time,
        )

        # Determinar estado final
        if errors and len(errors) > 0 and len(questions) == 0:
            self.status = BatchStatus.FAILED
        elif len(invalid_questions) > 0 and len(valid_questions) > 0:
            self.status = BatchStatus.PARTIAL
        else:
            self.status = BatchStatus.COMPLETED

        # Marcar secciones como procesadas
        for section in self.sections:
            section.mark_as_processed()

    def fail(self, error_message: str) -> None:
        """
        Marca el batch como fallido.

        Args:
            error_message: Mensaje de error
        """
        self.status = BatchStatus.FAILED
        self.error_message = error_message
        self.processed_at = datetime.now()

        # Marcar secciones con error
        for section in self.sections:
            section.mark_as_error(error_message)

    def get_sections_text(self, delimiter: str = "\n---\n") -> str:
        """
        Obtiene el texto combinado de todas las secciones.

        Args:
            delimiter: Delimitador entre secciones

        Returns:
            Texto combinado
        """
        texts = []
        for section in self.sections:
            header = f"[Sección {section.id}] {section.title} (Pág. {section.page})"
            texts.append(f"{header}\n{section.text}")
        return delimiter.join(texts)

    def to_dict(self) -> dict:
        """Convierte el batch a diccionario para serialización."""
        return {
            "id": self.id,
            "status": self.status.value,
            "size": self.size,
            "section_ids": self.section_ids,
            "total_text_length": self.total_text_length,
            "questions_count": len(self.questions),
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "result": {
                "questions_generated": self.result.questions_generated,
                "questions_valid": self.result.questions_valid,
                "questions_invalid": self.result.questions_invalid,
                "errors": self.result.errors,
                "warnings": self.result.warnings,
                "tokens_used": self.result.tokens_used,
                "cost_usd": self.result.cost_usd,
                "processing_time_seconds": self.result.processing_time_seconds,
            } if self.result else None,
            "error_message": self.error_message,
        }

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Batch):
            return False
        return self.id == other.id
