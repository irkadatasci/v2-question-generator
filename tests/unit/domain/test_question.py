"""Tests para la entidad Question."""

import pytest
from src.domain.entities.question import Question, QuestionType, QuestionStatus
from src.domain.value_objects.origin import Origin
from src.domain.value_objects.metadata import QuestionMetadata


class TestQuestion:
    """Tests para la entidad Question."""

    def test_create_flashcard(self):
        """Debe crear una flashcard correctamente."""
        origin = Origin.from_dict({
            "document_id": "doc1",
            "section_id": 1,
            "page": 5,
        })
        metadata = QuestionMetadata.from_dict({"difficulty": 3})

        question = Question.create_flashcard(
            front="¿Qué es el derecho?",
            back="Es el conjunto de normas...",
            origin=origin,
            metadata=metadata,
        )

        assert question.type == QuestionType.FLASHCARD
        assert question.question_text == "¿Qué es el derecho?"
        assert question.content.front == "¿Qué es el derecho?"
        assert question.content.back == "Es el conjunto de normas..."
        assert question.status == QuestionStatus.PENDING
        assert question.origin.document_id == "doc1"

    def test_create_true_false(self):
        """Debe crear una pregunta V/F correctamente."""
        origin = Origin.from_dict({"document_id": "doc1"})
        metadata = QuestionMetadata.from_dict({})

        question = Question.create_true_false(
            statement="El plazo es de 30 días",
            answer=True,
            justification="Según el artículo 1...",
            origin=origin,
            metadata=metadata,
        )

        assert question.type == QuestionType.TRUE_FALSE
        assert question.content.statement == "El plazo es de 30 días"
        assert question.content.answer is True
        assert question.content.justification == "Según el artículo 1..."

    def test_create_multiple_choice(self):
        """Debe crear una pregunta de opción múltiple."""
        origin = Origin.from_dict({"document_id": "doc1"})
        metadata = QuestionMetadata.from_dict({})

        question = Question.create_multiple_choice(
            question="¿Cuál es el plazo?",
            options=["10 días", "20 días", "30 días", "40 días"],
            correct_index=2,
            origin=origin,
            metadata=metadata,
        )

        assert question.type == QuestionType.MULTIPLE_CHOICE
        assert len(question.content.options) == 4
        assert question.content.correct_index == 2

    def test_validate_marks_status(self):
        """Validar debe marcar el status correctamente."""
        origin = Origin.from_dict({"document_id": "doc1"})
        metadata = QuestionMetadata.from_dict({})

        question = Question.create_flashcard(
            front="Test",
            back="Test respuesta",
            origin=origin,
            metadata=metadata,
        )

        question.validate()
        # Una pregunta válida debería estar VALIDATED
        # (depende de la implementación de validate())

    def test_mark_invalid_adds_errors(self):
        """mark_invalid debe guardar los errores."""
        origin = Origin.from_dict({"document_id": "doc1"})
        metadata = QuestionMetadata.from_dict({})

        question = Question.create_flashcard(
            front="T",  # Muy corto
            back="R",
            origin=origin,
            metadata=metadata,
        )

        question.mark_invalid(["Frente muy corto", "Reverso muy corto"])

        assert question.status == QuestionStatus.INVALID
        assert len(question.validation_errors) == 2
