"""
Service Interfaces - Contratos para servicios externos.

Los servicios abstraen la comunicación con sistemas externos,
permitiendo cambiar implementaciones sin afectar la lógica de negocio.
"""

from .llm_service import LLMService, LLMResponse
from .pdf_extractor_service import PDFExtractorService
from .classification_service import ClassificationService
from .prompt_service import PromptService

__all__ = [
    "LLMService",
    "LLMResponse",
    "PDFExtractorService",
    "ClassificationService",
    "PromptService",
]
