"""
LLM Service Implementation - Implementación del puerto LLMService.
"""

from typing import Any, Dict, List, Optional

from ...application.ports.services import LLMService, LLMResponse
from .backends.base import BaseLLMBackend, LLMConfig
from .factory import LLMFactory, LLMProvider


class LLMServiceImpl(LLMService):
    """
    Implementación concreta del servicio de LLM.

    Actúa como adapter entre el puerto LLMService y los backends concretos.
    Permite cambiar de proveedor sin afectar el resto de la aplicación.
    """

    def __init__(self, backend: BaseLLMBackend):
        """
        Args:
            backend: Backend de LLM a utilizar
        """
        self._backend = backend

    @classmethod
    def from_config(
        cls,
        provider: str,
        api_key: str,
        model: str = "",
        **kwargs,
    ) -> "LLMServiceImpl":
        """
        Factory method para crear el servicio desde configuración.

        Args:
            provider: Nombre del proveedor (kimi, groq, openai, ollama)
            api_key: API key del proveedor
            model: Modelo a usar (opcional, usa default)
            **kwargs: Argumentos adicionales para LLMConfig

        Returns:
            Instancia de LLMServiceImpl configurada
        """
        config = LLMConfig(
            api_key=api_key,
            model=model,
            **kwargs,
        )

        backend = LLMFactory.create_from_string(provider, config)
        return cls(backend)

    @property
    def provider_name(self) -> str:
        """Nombre del proveedor actual."""
        return self._backend.provider_name

    @property
    def model_name(self) -> str:
        """Nombre del modelo actual."""
        return self._backend.model_name

    @property
    def supports_context_caching(self) -> bool:
        """Indica si el backend soporta context caching."""
        return self._backend.supports_context_caching

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_tokens: int = 6000,
        response_format: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Genera una respuesta usando el LLM.
        
        Los parámetros temperature y max_tokens se usan para actualizar
        la configuración del backend, pero el método generate() del backend
        no los acepta como parámetros.
        """
        # Actualizar configuración del backend si se proporcionan valores diferentes
        if temperature != self._backend._config.temperature:
            self._backend._config.temperature = temperature
        if max_tokens != self._backend._config.max_tokens:
            self._backend._config.max_tokens = max_tokens
            
        # Llamar al backend sin pasar temperature/max_tokens como parámetros
        return self._backend.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            response_format=response_format or "text",
        )

    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 6000,
        **kwargs,
    ) -> List[LLMResponse]:
        """Genera respuestas para múltiples prompts."""
        # Actualizar configuración del backend si se proporcionan valores diferentes
        if temperature != self._backend._config.temperature:
            self._backend._config.temperature = temperature
        if max_tokens != self._backend._config.max_tokens:
            self._backend._config.max_tokens = max_tokens
            
        # Verificar si el backend soporta generate_batch
        if hasattr(self._backend, 'generate_batch'):
            return self._backend.generate_batch(
                prompts=prompts,
                system_prompt=system_prompt,
            )
        else:
            # Fallback: llamar generate() para cada prompt
            responses = []
            for prompt in prompts:
                response = self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                responses.append(response)
            return responses

    def verify_connection(self) -> bool:
        """Verifica conexión con el proveedor."""
        return self._backend.verify_connection()

    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso del backend."""
        return self._backend.get_usage_stats()

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estima costo de una llamada."""
        return self._backend.estimate_cost(prompt_tokens, completion_tokens)

    def count_tokens(self, text: str) -> int:
        """Cuenta tokens en un texto."""
        return self._backend.count_tokens(text)

    def get_context_window_size(self) -> int:
        """Obtiene el tamaño máximo de context window."""
        return self._backend.get_context_window_size()

    def switch_backend(self, backend: BaseLLMBackend) -> None:
        """
        Cambia el backend de LLM en runtime.
        """
        self._backend = backend

    def switch_provider(
        self,
        provider: str,
        api_key: str,
        model: str = "",
        **kwargs,
    ) -> None:
        """
        Cambia de proveedor en runtime.
        """
        config = LLMConfig(
            api_key=api_key,
            model=model,
            **kwargs,
        )
        self._backend = LLMFactory.create_from_string(provider, config)

    def get_backend_config(self) -> dict:
        """Retorna la configuración actual del backend."""
        return self._backend.get_config()