"""
Domain Entities - Objetos de negocio puros sin dependencias externas.

Las entidades representan los conceptos fundamentales del dominio:
- Document: Documento PDF fuente
- Section: Sección extraída del documento
- Question: Pregunta generada
- Batch: Grupo de secciones para procesamiento
"""

from .document import Document
from .section import Section
from .question import Question, QuestionType
from .batch import Batch

__all__ = [
    "Document",
    "Section",
    "Question",
    "QuestionType",
    "Batch",
]
