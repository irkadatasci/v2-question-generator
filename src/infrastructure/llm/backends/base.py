"""
Base LLM Backend - Clase base abstracta para backends de LLM.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json


@dataclass
class LLMConfig:
    """Configuración para un backend de LLM."""
    api_key: str = ""
    base_url: Optional[str] = None
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # Configuración específica de contexto
    context_caching: bool = False
    cache_ttl: int = 300

    # Headers adicionales
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convierte a diccionario (sin API key)."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "context_caching": self.context_caching,
        }


@dataclass
class LLMResponse:
    """Respuesta de un backend de LLM."""
    content: Any  # Puede ser string o dict/list (JSON parseado)
    raw_content: str  # Siempre string original

    # Métricas
    tokens_prompt: int = 0
    tokens_completion: int = 0
    tokens_total: int = 0

    # Costos
    cost_usd: float = 0.0

    # Timing
    latency_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    # Metadata
    model: str = ""
    provider: str = ""
    finish_reason: str = ""
    request_id: str = ""

    # Cache
    from_cache: bool = False
    cache_key: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convierte a diccionario serializable."""
        return {
            "content": self.content if isinstance(self.content, (str, dict, list)) else str(self.content),
            "tokens": {
                "prompt": self.tokens_prompt,
                "completion": self.tokens_completion,
                "total": self.tokens_total,
            },
            "cost_usd": self.cost_usd,
            "latency_seconds": self.latency_seconds,
            "model": self.model,
            "provider": self.provider,
            "finish_reason": self.finish_reason,
            "from_cache": self.from_cache,
        }


class BaseLLMBackend(ABC):
    """
    Clase base abstracta para backends de LLM.

    Define el contrato que todos los backends deben implementar.
    Usa el patrón Template Method para operaciones comunes.
    """

    def __init__(self, config: LLMConfig):
        """
        Args:
            config: Configuración del backend
        """
        self._config = config
        self._client = None
        self._cache: Dict[str, LLMResponse] = {}

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nombre del proveedor (ej: 'kimi', 'groq', 'openai')."""
        pass

    @property
    def model_name(self) -> str:
        """Nombre del modelo configurado."""
        return self._config.model

    @abstractmethod
    def _initialize_client(self) -> None:
        """Inicializa el cliente SDK específico del proveedor."""
        pass

    @abstractmethod
    def _call_api(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str,
    ) -> LLMResponse:
        """
        Realiza la llamada a la API del proveedor.

        Args:
            prompt: User prompt
            system_prompt: System prompt
            response_format: Formato esperado ('text' o 'json')

        Returns:
            LLMResponse con el resultado
        """
        pass

    @abstractmethod
    def verify_connection(self) -> bool:
        """Verifica que la conexión con el proveedor funciona."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Lista los modelos disponibles en este proveedor."""
        pass

    @abstractmethod
    def estimate_cost(self, tokens_prompt: int, tokens_completion: int) -> float:
        """
        Estima el costo de una llamada.

        Args:
            tokens_prompt: Tokens de entrada
            tokens_completion: Tokens de salida

        Returns:
            Costo estimado en USD
        """
        pass

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        response_format: str = "text",
    ) -> LLMResponse:
        """
        Genera una respuesta usando el LLM.

        Template Method que implementa:
        1. Verificación de inicialización
        2. Cache lookup (si habilitado)
        3. Llamada a API con reintentos
        4. Cache store (si habilitado)
        5. Parsing de JSON (si aplica)

        Args:
            prompt: User prompt
            system_prompt: System prompt
            response_format: 'text' o 'json'

        Returns:
            LLMResponse con el resultado
        """
        # Inicializar cliente si necesario
        if self._client is None:
            self._initialize_client()

        # Cache lookup
        if self._config.context_caching:
            cache_key = self._generate_cache_key(prompt, system_prompt)
            cached = self._cache.get(cache_key)
            if cached:
                cached.from_cache = True
                cached.cache_key = cache_key
                return cached

        # Llamada con reintentos
        last_error = None
        for attempt in range(self._config.retry_attempts):
            try:
                response = self._call_api(prompt, system_prompt, response_format)

                # Parsear JSON si es necesario
                if response_format == "json" and isinstance(response.content, str):
                    response.content = self._parse_json_response(response.content)

                # Cache store
                if self._config.context_caching:
                    self._cache[cache_key] = response
                    response.cache_key = cache_key

                return response

            except Exception as e:
                last_error = e
                if attempt < self._config.retry_attempts - 1:
                    import time
                    time.sleep(self._config.retry_delay * (attempt + 1))

        # Todos los reintentos fallaron
        raise ConnectionError(
            f"Falló después de {self._config.retry_attempts} intentos: {last_error}"
        )

    def _generate_cache_key(self, prompt: str, system_prompt: str) -> str:
        """Genera una clave de cache basada en los prompts."""
        import hashlib
        content = f"{self._config.model}:{system_prompt}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()

    def _parse_json_response(self, content: str) -> Any:
        """
        Parsea una respuesta JSON, manejando markdown code blocks.

        Args:
            content: Contenido a parsear

        Returns:
            Objeto Python parseado
        """
        # Intentar parseo directo
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Intentar extraer de markdown code block
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)

        # Fallback: retornar como string
        return content

    def clear_cache(self) -> None:
        """Limpia el cache de respuestas."""
        self._cache.clear()

    def get_config(self) -> Dict:
        """Retorna la configuración actual (sin datos sensibles)."""
        return self._config.to_dict()
