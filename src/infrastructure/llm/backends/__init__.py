"""
LLM Backends - Implementaciones concretas de backends de LLM.
"""

from .base import BaseLLMBackend, LLMConfig, LLMResponse
from .kimi import KimiBackend
from .groq import GroqBackend
from .openai import OpenAIBackend
from .ollama import OllamaBackend
from .ollama_cloud import OllamaCloudBackend

__all__ = [
    "BaseLLMBackend",
    "LLMConfig",
    "LLMResponse",
    "KimiBackend",
    "GroqBackend",
    "OpenAIBackend",
    "OllamaBackend",
    "OllamaCloudBackend",
]
