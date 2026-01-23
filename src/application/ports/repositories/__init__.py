"""
Repository Interfaces - Contratos para persistencia de datos.

Los repositorios abstraen el acceso a datos, permitiendo cambiar
la implementación (CSV, JSON, DB) sin afectar la lógica de negocio.
"""

from .section_repository import SectionRepository
from .question_repository import QuestionRepository
from .document_repository import DocumentRepository
from .experiment_repository import ExperimentRepository

__all__ = [
    "SectionRepository",
    "QuestionRepository",
    "DocumentRepository",
    "ExperimentRepository",
]
