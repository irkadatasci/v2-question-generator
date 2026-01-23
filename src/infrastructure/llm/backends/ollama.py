"""
Ollama Backend - Implementación para Ollama (local y cloud).
"""

import time
from typing import List, Optional

from .base import BaseLLMBackend, LLMConfig, LLMResponse


class OllamaBackend(BaseLLMBackend):
    """
    Backend para Ollama.

    Ollama permite ejecutar LLMs localmente o conectarse a instancias remotas.
    Ideal para:
    - Desarrollo y testing sin costos de API
    - Procesamiento offline
    - Privacidad de datos
    """

    # Modelos comunes (precios = 0 para local)
    MODELS = {
        "llama3.2": {"context": 131072, "price_input": 0, "price_output": 0},
        "llama3.1": {"context": 131072, "price_input": 0, "price_output": 0},
        "llama3.1:70b": {"context": 131072, "price_input": 0, "price_output": 0},
        "qwen2.5": {"context": 32768, "price_input": 0, "price_output": 0},
        "qwen2.5:32b": {"context": 32768, "price_input": 0, "price_output": 0},
        "qwen2.5-coder": {"context": 32768, "price_input": 0, "price_output": 0},
        "mistral": {"context": 32768, "price_input": 0, "price_output": 0},
        "mixtral": {"context": 32768, "price_input": 0, "price_output": 0},
        "gemma2": {"context": 8192, "price_input": 0, "price_output": 0},
        "phi3": {"context": 4096, "price_input": 0, "price_output": 0},
        "codellama": {"context": 16384, "price_input": 0, "price_output": 0},
    }

    DEFAULT_MODEL = "llama3.2"
    DEFAULT_BASE_URL = "http://localhost:11434"

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _initialize_client(self) -> None:
        """Inicializa el cliente Ollama."""
        try:
            import ollama
        except ImportError:
            raise ImportError("Se requiere ollama: pip install ollama")

        base_url = self._config.base_url or self.DEFAULT_BASE_URL

        # Ollama client usa OLLAMA_HOST
        import os
        os.environ["OLLAMA_HOST"] = base_url

        self._client = ollama
        self._base_url = base_url

    def _call_api(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str,
    ) -> LLMResponse:
        """Realiza llamada a Ollama."""
        start_time = time.time()

        model = self._config.model or self.DEFAULT_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Configurar opciones
        options = {
            "temperature": self._config.temperature,
            "num_predict": self._config.max_tokens,
        }

        # Llamada a Ollama
        kwargs = {
            "model": model,
            "messages": messages,
            "options": options,
        }

        if response_format == "json":
            kwargs["format"] = "json"

        response = self._client.chat(**kwargs)

        latency = time.time() - start_time

        content = response.get("message", {}).get("content", "")

        # Ollama puede proporcionar métricas de tokens
        eval_count = response.get("eval_count", 0)
        prompt_eval_count = response.get("prompt_eval_count", 0)

        return LLMResponse(
            content=content,
            raw_content=content,
            tokens_prompt=prompt_eval_count,
            tokens_completion=eval_count,
            tokens_total=prompt_eval_count + eval_count,
            cost_usd=0.0,  # Ollama local es gratis
            latency_seconds=latency,
            model=model,
            provider=self.provider_name,
            finish_reason="done" if response.get("done") else "",
        )

    def verify_connection(self) -> bool:
        """Verifica conexión con Ollama."""
        try:
            if self._client is None:
                self._initialize_client()

            # Verificar que el servidor responde
            models = self._client.list()
            return True

        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Lista modelos disponibles (instalados localmente)."""
        try:
            if self._client is None:
                self._initialize_client()

            response = self._client.list()
            return [m.get("name", "") for m in response.get("models", [])]

        except Exception:
            return list(self.MODELS.keys())

    def estimate_cost(self, tokens_prompt: int, tokens_completion: int) -> float:
        """Ollama local es gratis."""
        return 0.0

    def pull_model(self, model_name: str) -> bool:
        """
        Descarga un modelo de Ollama.

        Args:
            model_name: Nombre del modelo a descargar

        Returns:
            True si la descarga fue exitosa
        """
        try:
            if self._client is None:
                self._initialize_client()

            self._client.pull(model_name)
            return True

        except Exception:
            return False

    def is_model_available(self, model_name: str) -> bool:
        """
        Verifica si un modelo está disponible localmente.

        Args:
            model_name: Nombre del modelo

        Returns:
            True si el modelo está instalado
        """
        available = self.get_available_models()
        return any(model_name in m for m in available)
