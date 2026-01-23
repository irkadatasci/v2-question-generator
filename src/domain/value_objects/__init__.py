"""
Value Objects - Objetos inmutables que representan valores del dominio.

Los value objects son objetos sin identidad propia, definidos solo por sus atributos.
Son inmutables y comparados por valor (no por referencia).
"""

from .coordinates import Coordinates
from .classification import Classification, ClassificationResult, ClassificationMetrics
from .origin import Origin
from .metadata import QuestionMetadata, Difficulty

__all__ = [
    "Coordinates",
    "Classification",
    "ClassificationResult",
    "ClassificationMetrics",
    "Origin",
    "QuestionMetadata",
    "Difficulty",
]
