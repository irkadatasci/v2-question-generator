"""
LLM Factory - Factory para crear backends de LLM.
"""

from enum import Enum
from typing import Dict, Optional, Type

from .backends.base import BaseLLMBackend, LLMConfig
from .backends.kimi import KimiBackend
from .backends.groq import GroqBackend
from .backends.openai import OpenAIBackend
from .backends.ollama import OllamaBackend
from .backends.ollama_cloud import OllamaCloudBackend


class LLMProvider(Enum):
    """Proveedores de LLM disponibles."""
    KIMI = "kimi"
    GROQ = "groq"
    OPENAI = "openai"
    OLLAMA = "ollama"
    OLLAMA_CLOUD = "ollama_cloud"


class LLMFactory:
    """
    Factory para crear instancias de backends de LLM.

    Implementa el patrón Factory Method para abstraer la creación
    de backends específicos.

    Uso:
        config = LLMConfig(api_key="...", model="gpt-4o-mini")
        backend = LLMFactory.create(LLMProvider.OPENAI, config)
    """

    # Registro de backends
    _backends: Dict[LLMProvider, Type[BaseLLMBackend]] = {
        LLMProvider.KIMI: KimiBackend,
        LLMProvider.GROQ: GroqBackend,
        LLMProvider.OPENAI: OpenAIBackend,
        LLMProvider.OLLAMA: OllamaBackend,
        LLMProvider.OLLAMA_CLOUD: OllamaCloudBackend,
    }

    @classmethod
    def create(
        cls,
        provider: LLMProvider,
        config: LLMConfig,
    ) -> BaseLLMBackend:
        """
        Crea una instancia de backend para el proveedor especificado.

        Args:
            provider: Proveedor de LLM
            config: Configuración del backend

        Returns:
            Instancia de backend configurada

        Raises:
            ValueError: Si el proveedor no está registrado
        """
        backend_class = cls._backends.get(provider)

        if backend_class is None:
            available = [p.value for p in cls._backends.keys()]
            raise ValueError(
                f"Proveedor '{provider.value}' no soportado. "
                f"Disponibles: {available}"
            )

        return backend_class(config)

    @classmethod
    def create_from_string(
        cls,
        provider_name: str,
        config: LLMConfig,
    ) -> BaseLLMBackend:
        """
        Crea un backend a partir del nombre del proveedor como string.

        Args:
            provider_name: Nombre del proveedor (ej: "openai", "groq")
            config: Configuración del backend

        Returns:
            Instancia de backend configurada
        """
        try:
            provider = LLMProvider(provider_name.lower())
        except ValueError:
            available = [p.value for p in LLMProvider]
            raise ValueError(
                f"Proveedor '{provider_name}' no reconocido. "
                f"Disponibles: {available}"
            )

        return cls.create(provider, config)

    @classmethod
    def register_backend(
        cls,
        provider: LLMProvider,
        backend_class: Type[BaseLLMBackend],
    ) -> None:
        """
        Registra un nuevo backend (extensibilidad).

        Args:
            provider: Identificador del proveedor
            backend_class: Clase del backend
        """
        cls._backends[provider] = backend_class

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Lista los proveedores disponibles."""
        return [p.value for p in cls._backends.keys()]

    @classmethod
    def get_default_model(cls, provider: LLMProvider) -> str:
        """
        Obtiene el modelo por defecto de un proveedor.

        Args:
            provider: Proveedor de LLM

        Returns:
            Nombre del modelo por defecto
        """
        defaults = {
            LLMProvider.KIMI: KimiBackend.DEFAULT_MODEL,
            LLMProvider.GROQ: GroqBackend.DEFAULT_MODEL,
            LLMProvider.OPENAI: OpenAIBackend.DEFAULT_MODEL,
            LLMProvider.OLLAMA: OllamaBackend.DEFAULT_MODEL,
            LLMProvider.OLLAMA_CLOUD: OllamaCloudBackend.DEFAULT_MODEL,
        }
        return defaults.get(provider, "")

    @classmethod
    def get_available_models(cls, provider: LLMProvider) -> list[str]:
        """
        Obtiene los modelos disponibles de un proveedor.

        Args:
            provider: Proveedor de LLM

        Returns:
            Lista de modelos disponibles
        """
        models_map = {
            LLMProvider.KIMI: list(KimiBackend.MODELS.keys()),
            LLMProvider.GROQ: list(GroqBackend.MODELS.keys()),
            LLMProvider.OPENAI: list(OpenAIBackend.MODELS.keys()),
            LLMProvider.OLLAMA: list(OllamaBackend.MODELS.keys()),
            LLMProvider.OLLAMA_CLOUD: list(OllamaCloudBackend.MODELS.keys()),
        }
        return models_map.get(provider, [])
