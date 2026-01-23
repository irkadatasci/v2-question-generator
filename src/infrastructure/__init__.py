"""
Infrastructure Layer - Implementaciones concretas de puertos.

Esta capa contiene los adaptadores que implementan los puertos
definidos en la capa de aplicación:

- llm/: Backends de LLM (Kimi, Groq, OpenAI, Ollama)
- pdf/: Extracción de PDF (spacy-layout)
- persistence/: Repositorios (CSV, JSON)
- classification/: Clasificación semántica
- config/: Sistema de configuración
"""

from .llm import (
    LLMFactory,
    LLMProvider,
    LLMServiceImpl,
    BaseLLMBackend,
    LLMConfig,
)
from .pdf import PDFExtractorServiceImpl
from .persistence import (
    SectionRepositoryCSV,
    QuestionRepositoryJSON,
    DocumentRepositoryJSON,
    ExperimentRepositoryJSON,
)
from .classification import SemanticClassificationService

__all__ = [
    # LLM
    "LLMFactory",
    "LLMProvider",
    "LLMServiceImpl",
    "BaseLLMBackend",
    "LLMConfig",
    # PDF
    "PDFExtractorServiceImpl",
    # Classification
    "SemanticClassificationService",
    # Persistence
    "SectionRepositoryCSV",
    "QuestionRepositoryJSON",
    "DocumentRepositoryJSON",
    "ExperimentRepositoryJSON",
]
