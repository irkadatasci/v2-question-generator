"""
Domain Layer - Entidades y lógica de negocio central.

Esta capa contiene:
- entities/: Objetos de dominio (Document, Section, Question)
- value_objects/: Objetos de valor (Classification, Coordinates)
- exceptions/: Excepciones de dominio
- services/: Servicios de dominio
"""

from .entities import (
    Document,
    Section,
    Question,
    Batch,
)
from .value_objects import (
    Classification,
    Coordinates,
    QuestionMetadata,
    Origin,
)

__all__ = [
    # Entities
    "Document",
    "Section",
    "Question",
    "Batch",
    # Value Objects
    "Classification",
    "Coordinates",
    "QuestionMetadata",
    "Origin",
]