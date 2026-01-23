"""
LLM Infrastructure - Adaptadores para servicios de LLM.

Implementa el patrón Strategy + Factory para backends intercambiables:
- KimiBackend: Moonshot AI (Kimi)
- GroqBackend: Groq Cloud
- OpenAIBackend: OpenAI API
- OllamaBackend: Ollama (local y cloud)
"""

from .backends.base import BaseLLMBackend, LLMConfig, LLMResponse
from .backends.kimi import KimiBackend
from .backends.groq import GroqBackend
from .backends.openai import OpenAIBackend
from .backends.ollama import OllamaBackend
from .factory import LLMFactory, LLMProvider
from .service import LLMServiceImpl

__all__ = [
    # Base
    "BaseLLMBackend",
    "LLMConfig",
    "LLMResponse",
    # Backends
    "KimiBackend",
    "GroqBackend",
    "OpenAIBackend",
    "OllamaBackend",
    # Factory
    "LLMFactory",
    "LLMProvider",
    # Service
    "LLMServiceImpl",
]
