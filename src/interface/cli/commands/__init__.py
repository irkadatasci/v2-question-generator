"""
CLI Commands - Comandos de la CLI.
"""

from .extract import ExtractCommand
from .classify import ClassifyCommand
from .generate import GenerateCommand
from .validate import ValidateCommand
from .pipeline import PipelineCommand
from .config import ConfigCommand

__all__ = [
    "ExtractCommand",
    "ClassifyCommand",
    "GenerateCommand",
    "ValidateCommand",
    "PipelineCommand",
    "ConfigCommand",
]
