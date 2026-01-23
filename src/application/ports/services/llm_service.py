"""
LLM Service Interface - Contrato para backends de LLM.

Esta es la interface central del patrón Strategy para los backends LLM.
Todas las implementaciones (Kimi, Groq, OpenAI, Ollama) deben cumplir
este contrato.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """
    Respuesta estandarizada de un LLM.

    Attributes:
        content: Contenido de la respuesta (texto o JSON parseado)
        raw_content: Contenido crudo sin parsear
        model: Modelo utilizado
        tokens_prompt: Tokens en el prompt
        tokens_completion: Tokens en la respuesta
        tokens_total: Tokens totales
        cost_usd: Costo estimado en USD
        latency_seconds: Tiempo de respuesta
        cache_hit: Si hubo cache hit (para context caching)
        finish_reason: Razón de finalización
        metadata: Metadata adicional del proveedor
    """

    content: Any  # str | Dict | List
    raw_content: str
    model: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_total: int = 0
    cost_usd: float = 0.0
    latency_seconds: float = 0.0
    cache_hit: bool = False
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Indica si la respuesta fue exitosa."""
        return self.finish_reason == "stop" and self.content is not None


class LLMService(ABC):
    """
    Interface abstracta para servicios de LLM.

    Define el contrato que deben implementar todos los backends LLM.
    Usa el patrón Strategy para permitir cambiar backends en runtime.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nombre del proveedor (kimi, groq, openai, ollama, etc.)."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nombre del modelo actual."""
        pass

    @property
    @abstractmethod
    def supports_context_caching(self) -> bool:
        """Indica si el backend soporta context caching."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 6000,
        response_format: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Genera una respuesta del LLM.

        Args:
            prompt: Prompt del usuario
            system_prompt: System prompt
            temperature: Temperatura (0.0-1.0)
            max_tokens: Máximo de tokens en respuesta
            response_format: Formato de respuesta ("json" para JSON mode)
            **kwargs: Argumentos adicionales específicos del backend

        Returns:
            LLMResponse con la respuesta estandarizada
        """
        pass

    @abstractmethod
    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 6000,
        **kwargs,
    ) -> List[LLMResponse]:
        """
        Genera respuestas para múltiples prompts.

        Args:
            prompts: Lista de prompts
            system_prompt: System prompt compartido
            temperature: Temperatura
            max_tokens: Máximo de tokens
            **kwargs: Argumentos adicionales

        Returns:
            Lista de LLMResponse
        """
        pass

    @abstractmethod
    def verify_connection(self) -> bool:
        """
        Verifica que la conexión con el backend esté funcionando.

        Returns:
            True si la conexión es válida
        """
        pass

    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso del backend.

        Returns:
            Diccionario con estadísticas (tokens, costos, etc.)
        """
        pass

    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estima el costo de una llamada.

        Args:
            prompt_tokens: Tokens estimados del prompt
            completion_tokens: Tokens estimados de la respuesta

        Returns:
            Costo estimado en USD
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en un texto.

        Args:
            text: Texto a contar

        Returns:
            Número estimado de tokens
        """
        pass

    @abstractmethod
    def get_context_window_size(self) -> int:
        """
        Obtiene el tamaño máximo de context window.

        Returns:
            Tamaño en tokens
        """
        pass

    def can_fit_in_context(self, system_prompt: str, user_prompt: str) -> bool:
        """
        Verifica si el prompt cabe en el context window.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            True si cabe en el context window
        """
        total_tokens = self.count_tokens(system_prompt) + self.count_tokens(user_prompt)
        # Dejar espacio para la respuesta (al menos 25% del context window)
        max_prompt_tokens = int(self.get_context_window_size() * 0.75)
        return total_tokens <= max_prompt_tokens
