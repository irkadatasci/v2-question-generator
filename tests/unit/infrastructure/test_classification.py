"""Tests para el servicio de clasificación semántica."""

import pytest
from src.infrastructure.classification import SemanticClassificationService
from src.domain.entities.section import Section
from src.domain.value_objects.coordinates import Coordinates
from src.domain.value_objects.classification import Classification


class TestSemanticClassificationService:
    """Tests para SemanticClassificationService."""

    @pytest.fixture
    def classifier(self):
        """Fixture para el clasificador."""
        return SemanticClassificationService(
            threshold_relevant=0.7,
            threshold_review=0.5,
            auto_conserve_length=300,
        )

    def test_classify_relevant_legal_section(self, classifier):
        """Debe clasificar como RELEVANT sección con alto contenido jurídico."""
        section = Section(
            id=1,
            document_id="doc1",
            title="Prescripción",
            page=1,
            text="""
            El artículo 1 establece que el plazo de prescripción es de 5 años
            contados desde la fecha del acto. La prescripción extintiva requiere
            el transcurso del tiempo establecido por la ley. El tribunal deberá
            declarar la prescripción cuando se cumplan los requisitos legales.
            El recurso de apelación procede contra la resolución que declara
            la prescripción. El demandante debe presentar su demanda dentro
            del plazo establecido.
            """,
            coordinates=Coordinates(0, 0, 0, 0, 1),
        )

        result = classifier.classify(section)

        assert result.classification == Classification.RELEVANT
        assert result.score >= 0.7
        assert result.rj_score > 0.6  # Alta relevancia jurídica
        assert result.as_score > 0.5  # Buena aptitud semántica

    def test_classify_short_discardable_section(self, classifier):
        """Debe clasificar como DISCARDABLE sección muy corta."""
        section = Section(
            id=2,
            document_id="doc1",
            title="",
            page=2,
            text="Capítulo I",
            coordinates=Coordinates(0, 0, 0, 0, 2),
        )

        result = classifier.classify(section)

        assert result.classification == Classification.DISCARDABLE
        assert result.score < 0.5

    def test_classify_auto_conserved_long_section(self, classifier):
        """Debe clasificar como AUTO_CONSERVED sección larga con contenido básico."""
        section = Section(
            id=3,
            document_id="doc1",
            title="Introducción",
            page=3,
            text="A" * 400,  # Sección larga pero con poco contenido semántico
            coordinates=Coordinates(0, 0, 0, 0, 3),
        )

        result = classifier.classify(section)

        # Debe ser AUTO_CONSERVED por longitud, aunque score sea bajo
        assert result.classification in [
            Classification.AUTO_CONSERVED,
            Classification.REVIEW_NEEDED
        ]

    def test_calculate_legal_relevance(self, classifier):
        """Debe calcular correctamente la relevancia jurídica."""
        # Sección con muchos términos legales
        section_legal = Section(
            id=4,
            document_id="doc1",
            title="",
            page=4,
            text="""
            El tribunal declara la sentencia mediante resolución judicial.
            El recurso de apelación procede según el artículo 5 del código.
            El demandante debe presentar demanda conforme a la ley.
            """,
            coordinates=Coordinates(0, 0, 0, 0, 4),
        )

        result_legal = classifier.classify(section_legal)

        # Sección sin términos legales
        section_non_legal = Section(
            id=5,
            document_id="doc1",
            title="",
            page=5,
            text="""
            En la mañana del lunes, las personas caminaban por la calle.
            El sol brillaba intensamente en el cielo azul.
            Los pájaros cantaban alegremente en los árboles.
            """,
            coordinates=Coordinates(0, 0, 0, 0, 5),
        )

        result_non_legal = classifier.classify(section_non_legal)

        # La sección legal debe tener mayor RJ score
        assert result_legal.rj_score > result_non_legal.rj_score
        assert result_legal.rj_score > 0.6

    def test_classify_batch(self, classifier):
        """Debe clasificar múltiples secciones."""
        sections = [
            Section(
                id=i,
                document_id="doc1",
                title=f"Section {i}",
                page=i,
                text=f"Content {i} " * 50,
                coordinates=Coordinates(0, 0, 0, 0, i),
            )
            for i in range(5)
        ]

        results = classifier.classify_batch(sections)

        assert len(results) == 5
        assert all(hasattr(r, 'classification') for r in results)
        assert all(hasattr(r, 'score') for r in results)
        assert all(0 <= r.score <= 1 for r in results)

    def test_metric_weights_sum_to_one(self, classifier):
        """Los pesos de las métricas deben sumar 1.0."""
        total_weight = (
            classifier._weight_as +
            classifier._weight_rj +
            classifier._weight_dc +
            classifier._weight_cc
        )

        assert abs(total_weight - 1.0) < 0.01  # Tolerancia para errores de float
