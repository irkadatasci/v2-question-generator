"""
Ollama Cloud Backend - Implementación para Ollama Cloud API.
"""

import json
import time
from typing import List, Optional

import requests

from .base import BaseLLMBackend, LLMConfig, LLMResponse


class OllamaCloudBackend(BaseLLMBackend):
    """
    Backend para Ollama Cloud.

    Ollama Cloud proporciona acceso a modelos de código abierto de alta calidad
    a través de una API cloud en ollama.com.

    Ideal para:
    - Acceso a modelos premium sin infraestructura local
    - Escalabilidad automática
    - Modelos especializados (DeepSeek, Ministral, etc.)
    """

    # Modelos disponibles en Ollama Cloud
    MODELS = {
        "deepseek-v3.1:671b": {"context": 4096, "price_input": 0.14, "price_output": 0.28},
        "ministral-3:14b-cloud": {"context": 32768, "price_input": 0.14, "price_output": 0.42},
        "ministral-8:26b-cloud": {"context": 32768, "price_input": 0.27, "price_output": 0.81},
        "gpt-oss:120b-cloud": {"context": 4096, "price_input": 0.20, "price_output": 0.60},
        "glm-4.6:cloud": {"context": 128000, "price_input": 0.005, "price_output": 0.025},
    }

    DEFAULT_MODEL = "ministral-3:14b-cloud"
    #DEFAULT_BASE_URL = "https://ollama.com/api"
    DEFAULT_BASE_URL = "http://localhost:11434/api"

    @property
    def provider_name(self) -> str:
        return "ollama_cloud"

    def _initialize_client(self) -> None:
        """Inicializa el cliente Ollama Cloud."""
        self._api_key = self._config.api_key or ""
        self._base_url = self._config.base_url or self.DEFAULT_BASE_URL
        
        if not self._api_key:
            raise ValueError("ollama_cloud requiere OLLAMA_CLOUD_API_KEY")
        
        # Asegurar que la URL termine con /
        if not self._base_url.endswith("/"):
            self._base_url += "/"

    def _call_api(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str,
    ) -> LLMResponse:
        """Realiza llamada a Ollama Cloud usando API directa."""
        start_time = time.time()

        model = self._config.model or self.DEFAULT_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Construir payload para Ollama Cloud API
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self._config.temperature,
                "num_predict": self._config.max_tokens,
            }
        }

        if response_format == "json":
            payload["format"] = "json"

        # Headers para la request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        # Realizar request a Ollama Cloud
        url = f"{self._base_url}chat"
        response = requests.post(url, json=payload, headers=headers, timeout=120)

        if response.status_code != 200:
            raise Exception(f"Error en Ollama Cloud API: {response.status_code} - {response.text}")

        response_data = response.json()
        latency = time.time() - start_time

        # Extraer contenido de la respuesta
        content = response_data.get("message", {}).get("content", "")

        # Estimar tokens (Ollama Cloud no siempre proporciona métricas exactas)
        prompt_tokens = len(prompt.split()) * 1.3  # Estimación
        completion_tokens = len(content.split()) * 1.3 if content else 0

        # Calcular costo
        cost = self._estimate_call_cost(model, int(prompt_tokens), int(completion_tokens))

        return LLMResponse(
            content=content,
            raw_content=content,
            tokens_prompt=int(prompt_tokens),
            tokens_completion=int(completion_tokens),
            tokens_total=int(prompt_tokens + completion_tokens),
            cost_usd=cost,
            latency_seconds=latency,
            model=model,
            provider=self.provider_name,
            finish_reason="done",
        )

    def verify_connection(self) -> bool:
        """Verifica conexión con Ollama Cloud."""
        try:
            if not hasattr(self, '_api_key'):
                self._initialize_client()

            # Test simple: hacer una llamada de prueba muy pequeña
            test_payload = {
                "model": self._config.model or self.DEFAULT_MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 10,
                }
            }

            headers = {
                "Authorization": f"Bearer {self._api_key}",
            }

            url = f"{self._base_url}tags"
            print(f"DEBUG: Verifying connection to {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"DEBUG: Response status: {response.status_code}")

            return response.status_code == 200

        except Exception as e:
            print(f"DEBUG: Connection verification exception: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """Lista modelos disponibles en Ollama Cloud."""
        return list(self.MODELS.keys())

    def estimate_cost(self, tokens_prompt: int, tokens_completion: int) -> float:
        """Estima costo de una llamada."""
        model = self._config.model or self.DEFAULT_MODEL
        return self._estimate_call_cost(model, tokens_prompt, tokens_completion)

    def _estimate_call_cost(
        self, model: str, tokens_prompt: int, tokens_completion: int
    ) -> float:
        """Calcula costo real de una llamada."""
        model_info = self.MODELS.get(model)
        if not model_info:
            # Modelo desconocido, asumir precios de Ministral
            return (tokens_prompt * 0.14 + tokens_completion * 0.42) / 1_000_000

        price_input = model_info.get("price_input", 0)
        price_output = model_info.get("price_output", 0)

        # Precios típicamente por millón de tokens
        return (tokens_prompt * price_input + tokens_completion * price_output) / 1_000_000
