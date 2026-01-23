"""
Kimi Backend - Implementación para Moonshot AI (Kimi).
"""

import time
from typing import List

from .base import BaseLLMBackend, LLMConfig, LLMResponse


class KimiBackend(BaseLLMBackend):
    """
    Backend para Moonshot AI (Kimi).

    Kimi es un LLM chino con soporte nativo para contextos largos
    y buena relación calidad/precio para procesamiento de texto en español.
    """

    # Modelos disponibles y sus límites de contexto
    MODELS = {
        "moonshot-v1-8k": {"context": 8192, "price_input": 0.012, "price_output": 0.012},
        "moonshot-v1-32k": {"context": 32768, "price_input": 0.024, "price_output": 0.024},
        "moonshot-v1-128k": {"context": 131072, "price_input": 0.06, "price_output": 0.06},
    }

    DEFAULT_MODEL = "moonshot-v1-128k"
    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"

    @property
    def provider_name(self) -> str:
        return "kimi"

    def _initialize_client(self) -> None:
        """Inicializa el cliente OpenAI compatible con Moonshot."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Se requiere openai>=1.0.0: pip install openai")

        base_url = self._config.base_url or self.DEFAULT_BASE_URL

        self._client = OpenAI(
            api_key=self._config.api_key,
            base_url=base_url,
            timeout=self._config.timeout,
        )

    def _call_api(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str,
    ) -> LLMResponse:
        """Realiza llamada a la API de Moonshot."""
        start_time = time.time()

        model = self._config.model or self.DEFAULT_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Configurar formato de respuesta
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        # Llamada a la API
        response = self._client.chat.completions.create(**kwargs)

        latency = time.time() - start_time

        # Extraer datos de respuesta
        choice = response.choices[0]
        content = choice.message.content or ""

        tokens_prompt = response.usage.prompt_tokens if response.usage else 0
        tokens_completion = response.usage.completion_tokens if response.usage else 0
        tokens_total = response.usage.total_tokens if response.usage else 0

        cost = self.estimate_cost(tokens_prompt, tokens_completion)

        return LLMResponse(
            content=content,
            raw_content=content,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            tokens_total=tokens_total,
            cost_usd=cost,
            latency_seconds=latency,
            model=model,
            provider=self.provider_name,
            finish_reason=choice.finish_reason or "",
            request_id=response.id if hasattr(response, 'id') else "",
        )

    def verify_connection(self) -> bool:
        """Verifica conexión con Moonshot."""
        try:
            if self._client is None:
                self._initialize_client()

            # Test simple
            response = self._client.chat.completions.create(
                model=self._config.model or self.DEFAULT_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return response.choices[0].message.content is not None

        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Lista modelos disponibles de Moonshot."""
        return list(self.MODELS.keys())

    def estimate_cost(self, tokens_prompt: int, tokens_completion: int) -> float:
        """Calcula costo basado en pricing de Moonshot (CNY convertido a USD)."""
        model = self._config.model or self.DEFAULT_MODEL
        pricing = self.MODELS.get(model, self.MODELS[self.DEFAULT_MODEL])

        # Precios por 1000 tokens (aproximación CNY a USD)
        cost_input = (tokens_prompt / 1000) * pricing["price_input"]
        cost_output = (tokens_completion / 1000) * pricing["price_output"]

        return round(cost_input + cost_output, 6)
