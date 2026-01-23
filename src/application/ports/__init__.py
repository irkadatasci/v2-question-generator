"""
Ports - Interfaces que definen los contratos entre capas.

Los puertos siguen el principio de inversión de dependencias:
- La capa de aplicación define las interfaces (puertos)
- La capa de infraestructura implementa los adaptadores

Tipos de puertos:
- Repositories: Interfaces para persistencia de datos
- Services: Interfaces para servicios externos (LLM, PDF)
"""

from .repositories import (
    SectionRepository,
    QuestionRepository,
    DocumentRepository,
    ExperimentRepository,
)
from .services import (
    LLMService,
    PDFExtractorService,
    ClassificationService,
    PromptService,
)

__all__ = [
    # Repositories
    "SectionRepository",
    "QuestionRepository",
    "DocumentRepository",
    "ExperimentRepository",
    # Services
    "LLMService",
    "PDFExtractorService",
    "ClassificationService",
    "PromptService",
]
