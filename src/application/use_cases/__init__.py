"""
Use Cases - Casos de uso que orquestan la lógica de negocio.

Los casos de uso son la capa de aplicación que:
- Reciben requests de la interface (CLI, API)
- Coordinan entidades de dominio
- Llaman a servicios externos a través de puertos
- Retornan resultados

Cada caso de uso representa una operación de negocio completa.
"""

from .extract_sections import ExtractSectionsUseCase, ExtractSectionsRequest, ExtractSectionsResult
from .classify_sections import ClassifySectionsUseCase, ClassifySectionsRequest, ClassifySectionsResult
from .generate_questions import GenerateQuestionsUseCase, GenerateQuestionsRequest, GenerateQuestionsResult
from .validate_questions import ValidateQuestionsUseCase, ValidateQuestionsRequest, ValidateQuestionsResult
from .run_pipeline import RunPipelineUseCase, RunPipelineRequest, RunPipelineResult

__all__ = [
    # Extract
    "ExtractSectionsUseCase",
    "ExtractSectionsRequest",
    "ExtractSectionsResult",
    # Classify
    "ClassifySectionsUseCase",
    "ClassifySectionsRequest",
    "ClassifySectionsResult",
    # Generate
    "GenerateQuestionsUseCase",
    "GenerateQuestionsRequest",
    "GenerateQuestionsResult",
    # Validate
    "ValidateQuestionsUseCase",
    "ValidateQuestionsRequest",
    "ValidateQuestionsResult",
    # Pipeline
    "RunPipelineUseCase",
    "RunPipelineRequest",
    "RunPipelineResult",
]
