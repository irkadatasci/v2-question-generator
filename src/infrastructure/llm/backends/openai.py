"""
OpenAI Backend - Implementación para OpenAI API.
"""

import time
from typing import List

from .base import BaseLLMBackend, LLMConfig, LLMResponse


class OpenAIBackend(BaseLLMBackend):
    """
    Backend para OpenAI API.

    OpenAI ofrece modelos de alta calidad (GPT-4, GPT-4o, GPT-3.5).
    Mayor costo pero excelente calidad de respuestas.
    """

    # Modelos disponibles y sus precios (USD por millón de tokens)
    MODELS = {
        "gpt-4o": {"context": 128000, "price_input": 2.50, "price_output": 10.00},
        "gpt-4o-mini": {"context": 128000, "price_input": 0.15, "price_output": 0.60},
        "gpt-4-turbo": {"context": 128000, "price_input": 10.00, "price_output": 30.00},
        "gpt-4": {"context": 8192, "price_input": 30.00, "price_output": 60.00},
        "gpt-3.5-turbo": {"context": 16385, "price_input": 0.50, "price_output": 1.50},
        "o1-preview": {"context": 128000, "price_input": 15.00, "price_output": 60.00},
        "o1-mini": {"context": 128000, "price_input": 3.00, "price_output": 12.00},
    }

    DEFAULT_MODEL = "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        return "openai"

    def _initialize_client(self) -> None:
        """Inicializa el cliente OpenAI."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Se requiere openai>=1.0.0: pip install openai")

        kwargs = {
            "api_key": self._config.api_key,
            "timeout": self._config.timeout,
        }

        if self._config.base_url:
            kwargs["base_url"] = self._config.base_url

        self._client = OpenAI(**kwargs)

    def _call_api(
        self,
        prompt: str,
        system_prompt: str,
        response_format: str,
    ) -> LLMResponse:
        """Realiza llamada a la API de OpenAI."""
        start_time = time.time()

        model = self._config.model or self.DEFAULT_MODEL

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
        }

        # Modelos o1 no soportan system prompt ni temperature
        if model.startswith("o1"):
            if system_prompt:
                # Incorporar system prompt en el user message
                messages = [{
                    "role": "user",
                    "content": f"{system_prompt}\n\n{prompt}"
                }]
                kwargs["messages"] = messages
            del kwargs["temperature"]

        if response_format == "json" and not model.startswith("o1"):
            kwargs["response_format"] = {"type": "json_object"}

        response = self._client.chat.completions.create(**kwargs)

        latency = time.time() - start_time

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
        """Verifica conexión con OpenAI."""
        try:
            if self._client is None:
                self._initialize_client()

            response = self._client.chat.completions.create(
                model=self._config.model or self.DEFAULT_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return response.choices[0].message.content is not None

        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Lista modelos disponibles de OpenAI."""
        return list(self.MODELS.keys())

    def estimate_cost(self, tokens_prompt: int, tokens_completion: int) -> float:
        """Calcula costo basado en pricing de OpenAI."""
        model = self._config.model or self.DEFAULT_MODEL
        pricing = self.MODELS.get(model, self.MODELS[self.DEFAULT_MODEL])

        # Precios por millón de tokens
        cost_input = (tokens_prompt / 1_000_000) * pricing["price_input"]
        cost_output = (tokens_completion / 1_000_000) * pricing["price_output"]

        return round(cost_input + cost_output, 6)
