"""
Semantic Classification Service - Clasificador semántico con 4 métricas.

Implementa el algoritmo de clasificación con:
- AS (30%): Aptitud Semántica
- RJ (40%): Relevancia Jurídica
- DC (20%): Densidad Conceptual
- CC (10%): Claridad Contextual
"""

import re
from collections import Counter
from typing import Dict, List, Set

from ...application.ports.services import ClassificationService
from ...domain.entities.section import Section
from ...domain.value_objects.classification import Classification, ClassificationResult, ClassificationMetrics


class SemanticClassificationService(ClassificationService):
    """
    Clasificador semántico basado en 4 métricas.

    Evalúa cada sección para determinar si es apta para generar preguntas.
    """

    # Términos jurídicos clave para RJ
    LEGAL_TERMS = {
        # Términos generales
        "artículo", "ley", "decreto", "norma", "reglamento", "código",
        "constitución", "jurisprudencia", "sentencia", "resolución",

        # Conceptos jurídicos
        "derecho", "deber", "obligación", "facultad", "competencia",
        "responsabilidad", "sanción", "multa", "pena", "delito",

        # Procedimientos
        "recurso", "apelación", "demanda", "querella", "denuncia",
        "proceso", "juicio", "instancia", "procedimiento",

        # Sujetos
        "tribunal", "juez", "parte", "demandante", "demandado",
        "acusado", "imputado", "fiscal", "abogado",

        # Efectos jurídicos
        "nulo", "válido", "vigente", "derogado", "modificado",
        "aplicable", "exigible", "prescrito", "caducado",

        # Plazos
        "plazo", "término", "día", "hábil", "inhábil", "mes", "año",
        "vencimiento", "prórroga", "suspensión", "interrupción",
    }

    # Conectores y estructuras para CC
    CLARITY_INDICATORS = {
        # Conectores lógicos
        "por lo tanto", "en consecuencia", "debido a", "dado que",
        "puesto que", "ya que", "porque", "así que",

        # Enumeraciones
        "primero", "segundo", "tercero", "finalmente",
        "en primer lugar", "en segundo lugar", "por último",

        # Definiciones
        "se entiende por", "es decir", "esto es", "a saber",
        "se define como", "consiste en", "significa",

        # Excepciones y condiciones
        "salvo", "excepto", "sin perjuicio", "a menos que",
        "siempre que", "cuando", "si", "en caso de",
    }

    # Patrones de referencias para DC
    REFERENCE_PATTERNS = [
        r"artículo\s+\d+",
        r"inciso\s+\w+",
        r"párrafo\s+\d+",
        r"literal\s+\w+",
        r"numeral\s+\d+",
        r"capítulo\s+[IVX]+",
        r"título\s+[IVX]+",
        r"ley\s+\d+",
        r"decreto\s+\d+",
    ]

    @property
    def classifier_name(self) -> str:
        return "semantic-rules-v2"

    def __init__(
        self,
        threshold_relevant: float = 0.7,
        threshold_review: float = 0.5,
        auto_conserve_length: int = 300,
    ):
        """
        Args:
            threshold_relevant: Umbral para RELEVANT
            threshold_review: Umbral para REVIEW_NEEDED
            auto_conserve_length: Longitud mínima para AUTO_CONSERVED
        """
        self._threshold_relevant = threshold_relevant
        self._threshold_review = threshold_review
        self._auto_conserve_length = auto_conserve_length

        # Pesos de las métricas
        self._weight_as = 0.30
        self._weight_rj = 0.40
        self._weight_dc = 0.20
        self._weight_cc = 0.10

    def set_thresholds(
        self,
        relevant: float = 0.7,
        review: float = 0.5,
        auto_conserve_length: int = 300,
    ) -> None:
        """Configura umbrales de clasificación."""
        self._threshold_relevant = relevant
        self._threshold_review = review
        self._auto_conserve_length = auto_conserve_length

    def get_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales actuales."""
        return {
            "relevant": self._threshold_relevant,
            "review": self._threshold_review,
            "auto_conserve_length": self._auto_conserve_length,
        }

    def set_weights(
        self,
        semantic_autonomy: float = 0.30,
        legal_relevance: float = 0.40,
        concept_density: float = 0.20,
        context_coherence: float = 0.10,
    ) -> None:
        """Configura los pesos de las métricas."""
        self._weight_as = semantic_autonomy
        self._weight_rj = legal_relevance
        self._weight_dc = concept_density
        self._weight_cc = context_coherence

    def get_weights(self) -> Dict[str, float]:
        """Obtiene los pesos actuales de las métricas."""
        return {
            "semantic_autonomy": self._weight_as,
            "legal_relevance": self._weight_rj,
            "concept_density": self._weight_dc,
            "context_coherence": self._weight_cc,
        }

    def add_domain_terms(self, terms: Dict[str, float]) -> None:
        """Agrega términos del dominio para relevancia."""
        self.LEGAL_TERMS.update(terms.keys())

    def get_domain_terms(self) -> Dict[str, float]:
        """Obtiene los términos del dominio configurados."""
        return {term: 1.0 for term in self.LEGAL_TERMS}

    def classify(self, section: Section) -> ClassificationResult:
        """
        Clasifica una sección individual.

        Args:
            section: Sección a clasificar

        Returns:
            ClassificationResult con clasificación y métricas
        """
        metrics = self.calculate_metrics(section.text)

        # Score final ponderado usando los nombres correctos
        final_score = (
            metrics.semantic_autonomy * self._weight_as +
            metrics.legal_relevance * self._weight_rj +
            metrics.concept_density * self._weight_dc +
            metrics.context_coherence * self._weight_cc
        )

        # Determinar clasificación
        classification = self._determine_classification(
            section,
            final_score,
            metrics.semantic_autonomy,
            metrics.legal_relevance,
        )

        return ClassificationResult(
            classification=classification,
            score=final_score,
            metrics=metrics,
        )

    def classify_batch(self, sections: List[Section]) -> List[ClassificationResult]:
        """Clasifica múltiples secciones."""
        return [self.classify(section) for section in sections]

    def calculate_metrics(self, text: str) -> ClassificationMetrics:
        """Calcula las 4 métricas de clasificación para un texto."""
        as_score = self._calculate_semantic_aptitude(text)
        rj_score = self._calculate_legal_relevance(text)
        dc_score = self._calculate_conceptual_density(text)
        cc_score = self._calculate_contextual_clarity(text)
        
        return ClassificationMetrics(
            semantic_autonomy=as_score,
            legal_relevance=rj_score,
            concept_density=dc_score,
            context_coherence=cc_score,
        )

    def get_statistics(self, results: List[ClassificationResult]) -> Dict:
        """Obtiene estadísticas de clasificación."""
        if not results:
            return {}

        counts = Counter(r.classification for r in results)
        total = len(results)

        return {
            "total_sections": total,
            "relevant": counts.get(Classification.RELEVANT, 0),
            "review_needed": counts.get(Classification.REVIEW_NEEDED, 0),
            "auto_conserved": counts.get(Classification.AUTO_CONSERVED, 0),
            "discardable": counts.get(Classification.DISCARDABLE, 0),
            "avg_score": sum(r.score for r in results) / total,
        }

    def _calculate_semantic_aptitude(self, text: str) -> float:
        """
        Calcula AS (Aptitud Semántica) - 30%
        """
        text_lower = text.lower()
        length = len(text_lower)

        # Longitud óptima: 200-1500 caracteres
        if length < 100:
            length_score = 0.2
        elif length < 200:
            length_score = 0.5
        elif 200 <= length <= 1500:
            length_score = 1.0
        elif length <= 3000:
            length_score = 0.8
        else:
            length_score = 0.6

        # Diversidad léxica (ratio tipos/tokens)
        words = re.findall(r'\b\w+\b', text_lower)
        if not words:
            lexical_diversity = 0
        else:
            lexical_diversity = len(set(words)) / len(words)

        # Presencia de oraciones completas
        sentences = re.split(r'[.!?]+', text)
        complete_sentences = [s for s in sentences if len(s.strip()) > 20]
        sentence_score = min(1.0, len(complete_sentences) / 3)

        # Combinar sub-métricas
        as_score = (
            length_score * 0.4 +
            lexical_diversity * 0.3 +
            sentence_score * 0.3
        )

        return round(as_score, 4)

    def _calculate_legal_relevance(self, text: str) -> float:
        """
        Calcula RJ (Relevancia Jurídica) - 40%
        """
        text_lower = text.lower()

        # Contar términos jurídicos
        legal_term_count = sum(
            text_lower.count(term) for term in self.LEGAL_TERMS
        )

        # Normalizar por longitud del texto
        words = len(re.findall(r'\b\w+\b', text_lower))
        if words == 0:
            term_density = 0
        else:
            term_density = min(1.0, legal_term_count / (words * 0.1))

        # Detectar citas legales explícitas
        citations = 0
        for pattern in self.REFERENCE_PATTERNS:
            citations += len(re.findall(pattern, text_lower, re.IGNORECASE))

        citation_score = min(1.0, citations / 3)

        # Detectar estructura de articulado
        has_article_structure = bool(re.search(
            r'artículo\s+\d+[.:]|^{\s*}?\d+\.',
            text_lower,
            re.IGNORECASE | re.MULTILINE
        ))
        structure_score = 1.0 if has_article_structure else 0.3

        # Combinar sub-métricas
        rj_score = (
            term_density * 0.5 +
            citation_score * 0.3 +
            structure_score * 0.2
        )

        return round(rj_score, 4)

    def _calculate_conceptual_density(self, text: str) -> float:
        """
        Calcula DC (Densidad Conceptual) - 20%
        """
        text_lower = text.lower()

        # Contar definiciones
        definitions = len(re.findall(
            r'se\s+(?:entiende|define|considera)\s+(?:por|como)',
            text_lower,
            re.IGNORECASE
        ))

        # Contar enumeraciones
        enumerations = len(re.findall(
            r'(?:^{\s*}?\d+\.|primero|segundo|tercero|a\)|b\)|c\))',
            text_lower,
            re.IGNORECASE | re.MULTILINE
        ))

        # Contar referencias cruzadas
        cross_references = sum(
            len(re.findall(pattern, text_lower, re.IGNORECASE))
            for pattern in self.REFERENCE_PATTERNS
        )

        # Normalizar
        total_concepts = definitions + enumerations + cross_references
        concept_score = min(1.0, total_concepts / 5)

        # Ratio de palabras clave
        words = re.findall(r'\b\w+\b', text_lower)
        if not words:
            keyword_ratio = 0
        else:
            keywords = sum(
                1 for word in words
                if word in self.LEGAL_TERMS or len(word) > 8
            )
            keyword_ratio = min(1.0, keywords / len(words) / 0.3)

        # Combinar
        dc_score = (
            concept_score * 0.6 +
            keyword_ratio * 0.4
        )

        return round(dc_score, 4)

    def _calculate_contextual_clarity(self, text: str) -> float:
        """
        Calcula CC (Claridad Contextual) - 10%
        """
        # Presencia de título (no se puede evaluar solo con texto)
        title_score = 0.5

        # Conectores lógicos
        connector_count = sum(
            1 for connector in self.CLARITY_INDICATORS
            if connector in text.lower()
        )
        connector_score = min(1.0, connector_count / 3)

        # Estructura de párrafos
        paragraphs = text.split('\n\n')
        valid_paragraphs = [p for p in paragraphs if len(p.strip()) > 50]
        paragraph_score = min(1.0, len(valid_paragraphs) / 2)

        # Combinar
        cc_score = (
            title_score * 0.3 +
            connector_score * 0.4 +
            paragraph_score * 0.3
        )

        return round(cc_score, 4)

    def _determine_classification(
        self,
        section: Section,
        final_score: float,
        as_score: float,
        rj_score: float,
    ) -> Classification:
        """
        Determina la clasificación final.
        """
        # AUTO_CONSERVED: Secciones largas con contenido básico
        if section.text_length >= self._auto_conserve_length:
            if as_score >= 0.5:
                return Classification.AUTO_CONSERVED

        # RELEVANT: Score alto y relevancia jurídica significativa
        if final_score >= self._threshold_relevant and rj_score >= 0.6:
            return Classification.RELEVANT

        # REVIEW_NEEDED: Score medio
        if final_score >= self._threshold_review:
            return Classification.REVIEW_NEEDED

        # DISCARDABLE: Score bajo o secciones muy cortas
        if section.text_length < 100 or final_score < 0.3:
            return Classification.DISCARDABLE

        # Default: AUTO_CONSERVED para contenido intermedio
        return Classification.AUTO_CONSERVED