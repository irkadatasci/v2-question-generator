"""
Configuración común de pytest y fixtures globales.
"""

import pytest
from pathlib import Path
from src.domain.entities.section import Section
from src.domain.entities.question import Question, QuestionType
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.origin import Origin
from src.domain.value_objects.metadata import QuestionMetadata


@pytest.fixture
def sample_section():
    """Fixture: Sección de ejemplo."""
    return Section(
        id=1,
        document_id="doc_test_123",
        title="Prescripción",
        page=5,
        text="""
        El artículo 1 establece que el plazo de prescripción es de 5 años
        contados desde la fecha del acto. La prescripción extintiva requiere
        el transcurso del tiempo establecido por la ley.
        """,
        coordinates=Coordinates(x=100, y=200, width=400, height=50, page=5),
    )


@pytest.fixture
def sample_sections():
    """Fixture: Lista de secciones de ejemplo."""
    return [
        Section(
            id=i,
            document_id="doc_test_123",
            title=f"Section {i}",
            page=i,
            text=f"Content for section {i}. " * 20,
            coordinates=Coordinates(0, 0, 400, 50, i),
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def sample_origin():
    """Fixture: Origin de ejemplo."""
    return Origin.from_dict({
        "document_id": "doc_test_123",
        "section_id": 1,
        "page": 5,
        "title": "Prescripción",
    })


@pytest.fixture
def sample_metadata():
    """Fixture: QuestionMetadata de ejemplo."""
    return QuestionMetadata.from_dict({
        "difficulty": 3,
        "tags": ["derecho", "prescripción"],
        "subtype": "definition",
    })


@pytest.fixture
def sample_flashcard(sample_origin, sample_metadata):
    """Fixture: Flashcard de ejemplo."""
    return Question.create_flashcard(
        front="¿Qué es la prescripción?",
        back="Es la extinción de un derecho por el transcurso del tiempo.",
        origin=sample_origin,
        metadata=sample_metadata,
    )


@pytest.fixture
def sample_true_false(sample_origin, sample_metadata):
    """Fixture: Pregunta V/F de ejemplo."""
    return Question.create_true_false(
        statement="El plazo de prescripción es de 5 años",
        answer=True,
        justification="Según el artículo 1",
        origin=sample_origin,
        metadata=sample_metadata,
    )


@pytest.fixture
def sample_multiple_choice(sample_origin, sample_metadata):
    """Fixture: Pregunta de opción múltiple de ejemplo."""
    return Question.create_multiple_choice(
        question="¿Cuál es el plazo de prescripción?",
        options=["3 años", "5 años", "10 años", "15 años"],
        correct_index=1,
        origin=sample_origin,
        metadata=sample_metadata,
        justification="El artículo 1 establece 5 años",
    )


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture: Directorio temporal para tests."""
    return tmp_path


@pytest.fixture
def mock_llm_response():
    """Fixture: Respuesta simulada de LLM."""
    return {
        "preguntas": [
            {
                "contenido_tipo": {
                    "frente": "¿Qué es X?",
                    "reverso": "X es...",
                },
                "origen": {
                    "section_id": 1,
                    "page": 5,
                },
                "sm2_metadata": {
                    "difficulty": 3,
                    "tags": ["test"],
                },
            }
        ]
    }
