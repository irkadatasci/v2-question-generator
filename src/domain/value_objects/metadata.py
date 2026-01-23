"""
Metadata Value Object - Metadata SM-2 para preguntas.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union


class Difficulty(Enum):
    """Niveles de dificultad para repetición espaciada."""
    BASIC = "basico"
    INTERMEDIATE = "intermedio"
    ADVANCED = "avanzado"


class QuestionSubtype(Enum):
    """Subtipos de preguntas para categorización."""
    DEFINITION = "definicion"
    REQUIREMENT = "requisito"
    EXCEPTION = "excepcion"
    EFFECT = "efecto"
    COMPARISON = "comparacion"
    TIMELINE = "plazo"
    SUBJECT = "sujeto"
    PROCEDURE = "procedimiento"
    CLASSIFICATION = "clasificacion"
    CHARACTERISTIC = "caracteristica"
    EXAMPLE = "ejemplo"
    LIST = "lista"
    CONCEPT = "concept"
    CASE = "case"
    DEFINITION_EN = "definition"
    PROCEDURE_EN = "procedure"
    COMPARISON_EN = "comparison"


@dataclass(frozen=True)
class QuestionMetadata:
    """
    Value object que representa metadata SM-2 de una pregunta.

    Contiene información para optimizar la repetición espaciada
    y categorización de preguntas.

    Attributes:
        difficulty: Nivel de dificultad
        tags: Lista de etiquetas para categorización
        subtype: Subtipo de pregunta
        topic: Tema principal (opcional)
        related_concepts: Conceptos relacionados (opcional)
    """

    # Mapa de normalización para subtypes (inglés -> español)
    SUBTYPE_NORMALIZATION_MAP = {
        "definition": "definicion",
        "requirement": "requisito",
        "exception": "excepcion",
        "effect": "efecto",
        "comparison": "comparacion",
        "timeline": "plazo",
        "subject": "sujeto",
        "procedure": "procedimiento",
        "classification": "clasificacion",
        "characteristic": "caracteristica",
        "example": "ejemplo",
        "list": "lista",
        "concept": "concept",
        "case": "case",
    }

    difficulty: Difficulty
    tags: tuple  # Tuple para ser hashable (frozen dataclass)
    subtype: QuestionSubtype
    topic: Optional[str] = None
    related_concepts: tuple = field(default_factory=tuple)

    @classmethod
    def _normalize_subtype(cls, value: str) -> str:
        """
        Normaliza valores de subtype, mapeando inglés a español cuando sea necesario.

        Args:
            value: Valor del subtype (puede ser en inglés o español)

        Returns:
            Valor normalizado
        """
        value_lower = value.lower().strip()
        return cls.SUBTYPE_NORMALIZATION_MAP.get(value_lower, value_lower)

    @classmethod
    def create(
        cls,
        difficulty: Union[str, Difficulty],
        tags: List[str],
        subtype: Union[str, QuestionSubtype],
        topic: Optional[str] = None,
        related_concepts: Optional[List[str]] = None,
    ) -> "QuestionMetadata":
        """
        Factory method para crear QuestionMetadata con conversión automática.

        Args:
            difficulty: Dificultad (string o enum)
            tags: Lista de tags
            subtype: Subtipo (string o enum)
            topic: Tema principal
            related_concepts: Conceptos relacionados

        Returns:
            Nueva instancia de QuestionMetadata
        """
        # Convertir difficulty
        if isinstance(difficulty, str):
            difficulty = Difficulty(difficulty.lower())
        elif isinstance(difficulty, int):
            # Mapear números a dificultades (1=basico, 2=intermedio, 3=avanzado, 4+=avanzado)
            difficulty_map = {
                0: Difficulty.BASIC,
                1: Difficulty.BASIC,
                2: Difficulty.INTERMEDIATE,
                3: Difficulty.ADVANCED,
            }
            difficulty = difficulty_map.get(difficulty, Difficulty.INTERMEDIATE)

        # Convertir subtype con normalización
        if isinstance(subtype, str):
            normalized_subtype = cls._normalize_subtype(subtype)
            try:
                subtype = QuestionSubtype(normalized_subtype)
            except ValueError:
                # Si aún no es válido, intentar con el valor original
                subtype = QuestionSubtype(subtype.lower())

        # Normalizar tags
        normalized_tags = tuple(
            tag.lower().replace(" ", "_").strip()
            for tag in tags
            if tag.strip()
        )

        # Convertir related_concepts a tuple
        related = tuple(related_concepts) if related_concepts else tuple()

        return cls(
            difficulty=difficulty,
            tags=normalized_tags,
            subtype=subtype,
            topic=topic,
            related_concepts=related,
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "QuestionMetadata":
        """
        Crea QuestionMetadata desde un diccionario.

        Args:
            data: Diccionario con metadata

        Returns:
            Nueva instancia de QuestionMetadata
        """
        return cls.create(
            difficulty=data.get("dificultad", data.get("difficulty", "basico")),
            tags=data.get("tags", []),
            subtype=data.get("subtipo", data.get("subtype", "definicion")),
            topic=data.get("tema", data.get("topic")),
            related_concepts=data.get("conceptos_relacionados", data.get("related_concepts")),
        )

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        result = {
            "dificultad": self.difficulty.value,
            "tags": list(self.tags),
            "subtipo": self.subtype.value,
        }

        if self.topic:
            result["tema"] = self.topic

        if self.related_concepts:
            result["conceptos_relacionados"] = list(self.related_concepts)

        return result

    def to_anki_tags(self) -> str:
        """Convierte tags a formato Anki (espacio separado)."""
        all_tags = list(self.tags)
        all_tags.append(f"difficulty::{self.difficulty.value}")
        all_tags.append(f"type::{self.subtype.value}")
        if self.topic:
            all_tags.append(f"topic::{self.topic}")
        return " ".join(all_tags)

    def matches_filter(
        self,
        difficulty: Optional[Difficulty] = None,
        tags: Optional[List[str]] = None,
        subtype: Optional[QuestionSubtype] = None,
    ) -> bool:
        """
        Verifica si la metadata coincide con filtros dados.

        Args:
            difficulty: Filtro de dificultad
            tags: Filtro de tags (cualquier match)
            subtype: Filtro de subtipo

        Returns:
            True si coincide con todos los filtros especificados
        """
        if difficulty and self.difficulty != difficulty:
            return False

        if subtype and self.subtype != subtype:
            return False

        if tags:
            # Al menos un tag debe coincidir
            if not any(tag in self.tags for tag in tags):
                return False

        return True

    @property
    def sm2_initial_factor(self) -> float:
        """
        Retorna el factor inicial SM-2 basado en la dificultad.

        Returns:
            Factor de facilidad inicial (2.5 es el valor por defecto SM-2)
        """
        factors = {
            Difficulty.BASIC: 2.7,       # Más fácil de recordar
            Difficulty.INTERMEDIATE: 2.5, # Factor estándar
            Difficulty.ADVANCED: 2.3,     # Más difícil
        }
        return factors.get(self.difficulty, 2.5)

    def __str__(self) -> str:
        return f"{self.difficulty.value} | {self.subtype.value} | {', '.join(self.tags)}"
