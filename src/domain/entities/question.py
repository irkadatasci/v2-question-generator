"""
Question Entity - Representa una pregunta generada.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..value_objects.origin import Origin
from ..value_objects.metadata import QuestionMetadata


class QuestionType(Enum):
    """Tipos de preguntas soportados."""
    FLASHCARD = "flashcards"
    TRUE_FALSE = "verdadero_falso"
    MULTIPLE_CHOICE = "opcion_multiple"
    CLOZE = "completar_espacios"


class QuestionStatus(Enum):
    """Estado de validación de una pregunta."""
    GENERATED = "generated"
    VALIDATED = "validated"
    INVALID = "invalid"
    EXPORTED = "exported"


@dataclass
class FlashcardContent:
    """Contenido específico para flashcards."""
    anverso: str  # Pregunta (frente)
    reverso: str  # Respuesta (reverso)


@dataclass
class TrueFalseContent:
    """Contenido específico para verdadero/falso."""
    pregunta: str           # Afirmación
    respuesta_correcta: bool # True o False
    explicacion: str        # Justificación de la respuesta


@dataclass
class MultipleChoiceContent:
    """Contenido específico para opción múltiple."""
    pregunta: str           # Pregunta
    opciones: List[str]      # 4 opciones
    respuesta_correcta: int  # Índice de la respuesta correcta (0-3)
    explicacion: str = ""    # Justificación opcional


@dataclass
class ClozeContent:
    """Contenido específico para completar espacios."""
    texto_con_espacios: str     # Texto con espacios {{blank}}
    respuestas_validas: List[str] # Respuestas válidas


@dataclass
class Question:
    """
    Entidad que representa una pregunta generada.

    Una pregunta es la unidad de salida del sistema. Puede ser de diferentes
    tipos (flashcard, true_false, multiple_choice, cloze) y mantiene
    trazabilidad completa hacia la sección origen.

    Attributes:
        id: Identificador único de la pregunta
        type: Tipo de pregunta
        question_text: Texto de la pregunta (campo unificado)
        content: Contenido específico según el tipo
        origin: Información de trazabilidad al origen
        metadata: Metadata SM-2 (dificultad, tags, subtipo)
        status: Estado de validación
        created_at: Fecha de creación
        validation_errors: Lista de errores de validación
    """

    id: str
    type: QuestionType
    question_text: str
    content: Any  # FlashcardContent | TrueFalseContent | MultipleChoiceContent | ClozeContent
    origin: Origin
    metadata: QuestionMetadata
    status: QuestionStatus = QuestionStatus.GENERATED
    created_at: datetime = field(default_factory=datetime.now)
    validation_errors: List[str] = field(default_factory=list)

    def mark_validated(self) -> None:
        """Marca la pregunta como validada."""
        self.status = QuestionStatus.VALIDATED
        self.validation_errors.clear()

    def mark_invalid(self, errors: List[str]) -> None:
        """Marca la pregunta como inválida con una lista de errores."""
        self.status = QuestionStatus.INVALID
        self.validation_errors = errors

    @classmethod
    def create_flashcard(
        cls,
        anverso: str,
        reverso: str,
        origin: Origin,
        metadata: QuestionMetadata,
    ) -> "Question":
        """Factory method para crear flashcard."""
        return cls(
            id=str(uuid4())[:8],
            type=QuestionType.FLASHCARD,
            question_text=anverso,
            content=FlashcardContent(anverso=anverso, reverso=reverso),
            origin=origin,
            metadata=metadata,
        )

    @classmethod
    def create_true_false(
        cls,
        pregunta: str,
        respuesta_correcta: bool,
        explicacion: str,
        origin: Origin,
        metadata: QuestionMetadata,
    ) -> "Question":
        """Factory method para crear verdadero/falso."""
        return cls(
            id=str(uuid4())[:8],
            type=QuestionType.TRUE_FALSE,
            question_text=pregunta,
            content=TrueFalseContent(
                pregunta=pregunta,
                respuesta_correcta=respuesta_correcta,
                explicacion=explicacion,
            ),
            origin=origin,
            metadata=metadata,
        )

    @classmethod
    def create_multiple_choice(
        cls,
        pregunta: str,
        opciones: List[str],
        respuesta_correcta: int,
        origin: Origin,
        metadata: QuestionMetadata,
        explicacion: str = "",
    ) -> "Question":
        """Factory method para crear opción múltiple."""
        return cls(
            id=str(uuid4())[:8],
            type=QuestionType.MULTIPLE_CHOICE,
            question_text=pregunta,
            content=MultipleChoiceContent(
                pregunta=pregunta,
                opciones=opciones,
                respuesta_correcta=respuesta_correcta,
                explicacion=explicacion,
            ),
            origin=origin,
            metadata=metadata,
        )

    @classmethod
    def create_cloze(
        cls,
        texto_con_espacios: str,
        respuestas_validas: List[str],
        origin: Origin,
        metadata: QuestionMetadata,
    ) -> "Question":
        """Factory method para crear cloze."""
        return cls(
            id=str(uuid4())[:8],
            type=QuestionType.CLOZE,
            question_text=texto_con_espacios,
            content=ClozeContent(
                texto_con_espacios=texto_con_espacios,
                respuestas_validas=respuestas_validas,
            ),
            origin=origin,
            metadata=metadata,
        )

    def validate(self) -> bool:
        """
        Valida la pregunta según su tipo.

        Returns:
            True si la pregunta es válida
        """
        self.validation_errors.clear()

        # Validaciones comunes
        if not self.question_text or not self.question_text.strip():
            self.validation_errors.append("Pregunta vacía")

        if not self.origin:
            self.validation_errors.append("Sin información de origen")

        # Validaciones específicas por tipo
        if self.type == QuestionType.FLASHCARD:
            self._validate_flashcard()
        elif self.type == QuestionType.TRUE_FALSE:
            self._validate_true_false()
        elif self.type == QuestionType.MULTIPLE_CHOICE:
            self._validate_multiple_choice()
        elif self.type == QuestionType.CLOZE:
            self._validate_cloze()

        if self.validation_errors:
            self.status = QuestionStatus.INVALID
            return False

        self.status = QuestionStatus.VALIDATED
        return True

    def _validate_flashcard(self) -> None:
        """Validaciones específicas para flashcard."""
        if not isinstance(self.content, FlashcardContent):
            self.validation_errors.append("Contenido no es FlashcardContent")
            return

        if not self.content.anverso.strip():
            self.validation_errors.append("Frente de flashcard vacío")

        if not self.content.reverso.strip():
            self.validation_errors.append("Reverso de flashcard vacío")

        if not self.content.anverso.rstrip().endswith("?"):
            self.validation_errors.append("Frente de flashcard debe terminar con '?'")

    def _validate_true_false(self) -> None:
        """Validaciones específicas para verdadero/falso."""
        if not isinstance(self.content, TrueFalseContent):
            self.validation_errors.append("Contenido no es TrueFalseContent")
            return

        if not self.content.pregunta.strip():
            self.validation_errors.append("Afirmación vacía")

        if not isinstance(self.content.respuesta_correcta, bool):
            self.validation_errors.append("Respuesta debe ser booleana")

    def _validate_multiple_choice(self) -> None:
        """Validaciones específicas para opción múltiple."""
        if not isinstance(self.content, MultipleChoiceContent):
            self.validation_errors.append("Contenido no es MultipleChoiceContent")
            return

        if not self.content.pregunta.strip():
            self.validation_errors.append("Pregunta vacía")

        if len(self.content.opciones) != 4:
            self.validation_errors.append("Debe tener exactamente 4 opciones")

        if not (0 <= self.content.respuesta_correcta <= 3):
            self.validation_errors.append("Índice de respuesta correcta inválido")

        # Verificar opciones duplicadas
        if len(set(self.content.opciones)) != len(self.content.opciones):
            self.validation_errors.append("Opciones duplicadas")

    def _validate_cloze(self) -> None:
        """Validaciones específicas para cloze."""
        if not isinstance(self.content, ClozeContent):
            self.validation_errors.append("Contenido no es ClozeContent")
            return

        if "{{" not in self.content.texto_con_espacios or "}}" not in self.content.texto_con_espacios:
            self.validation_errors.append("Texto debe contener espacios {{blank}}")

        if not self.content.respuestas_validas:
            self.validation_errors.append("Debe tener al menos una respuesta válida")

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la pregunta a diccionario para serialización JSON."""
        d = {
            "id": self.id,
            "tipo": self.type.value,
            "contenido_tipo": self._content_to_dict(),
            "origen": self.origin.to_dict(),
            "sm2_metadata": self.metadata.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "validation_errors": self.validation_errors,
        }
        
        # Compatibilidad LexQuest: campos redundantes en nivel superior si es necesario
        if self.type == QuestionType.FLASHCARD:
            d["anverso"] = self.content.anverso
            d["reverso"] = self.content.reverso
        else:
            d["pregunta"] = self.question_text
            
        return d

    def _content_to_dict(self) -> Dict[str, Any]:
        """Convierte el contenido específico a diccionario."""
        if self.type == QuestionType.FLASHCARD:
            return {"anverso": self.content.anverso, "reverso": self.content.reverso}
        elif self.type == QuestionType.TRUE_FALSE:
            return {
                "pregunta": self.content.pregunta,
                "respuesta_correcta": self.content.respuesta_correcta,
                "explicacion": self.content.explicacion,
            }
        elif self.type == QuestionType.MULTIPLE_CHOICE:
            return {
                "pregunta": self.content.pregunta,
                "opciones": self.content.opciones,
                "respuesta_correcta": self.content.respuesta_correcta,
                "explicacion": self.content.explicacion,
            }
        elif self.type == QuestionType.CLOZE:
            return {
                "texto_con_espacios": self.content.texto_con_espacios,
                "respuestas_validas": self.content.respuestas_validas,
            }
        return {}

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Question):
            return False
        return self.id == other.id
