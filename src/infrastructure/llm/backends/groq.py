"""
Groq Backend - Implementación para Groq Cloud.
"""

import time
from typing import List

from .base import BaseLLMBackend, LLMConfig, LLMResponse


class GroqBackend(BaseLLMBackend):
    """
    Backend para Groq Cloud.

    Groq ofrece inferencia ultra-rápida usando LPUs (Language Processing Units).
    Ideal para procesamiento batch donde la latencia es importante.
    """

    # Modelos disponibles y sus precios (USD por millón de tokens)
    MODELS = {
        "llama-3.3-70b-versatile": {"context": 32768, "price_input": 0.59, "price_output": 0.79},
        "llama-3.1-70b-versatile": {"context": 32768, "price_input": 0.59, "price_output": 0.79},
        "llama-3.1-8b-instant": {"context": 8192, "price_input": 0.05, "price_output": 0.08},
        "llama-3.2-90b-vision-preview": {"context": 8192, "price_input": 0.90, "price_output": 0.90},
        "mixtral-8x7b-32768": {"context": 32768, "price_input": 0.24, "price_output": 0.24},
        "gemma2-9b-it": {"context": 8192, "price_input": 0.20, "price_output": 0.20},
    }

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"

    @property
    def provider_name(self) -> str:
        return "groq"

    def _initialize_client(self) -> None:
        """Inicializa el cliente Groq (OpenAI-compatible)."""
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
        """Realiza llamada a la API de Groq."""
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

        if response_format == "json":
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
        """Verifica conexión con Groq."""
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
        """Lista modelos disponibles en Groq."""
        return list(self.MODELS.keys())

    def estimate_cost(self, tokens_prompt: int, tokens_completion: int) -> float:
        """Calcula costo basado en pricing de Groq."""
        model = self._config.model or self.DEFAULT_MODEL
        pricing = self.MODELS.get(model, self.MODELS[self.DEFAULT_MODEL])

        # Precios por millón de tokens
        cost_input = (tokens_prompt / 1_000_000) * pricing["price_input"]
        cost_output = (tokens_completion / 1_000_000) * pricing["price_output"]

        return round(cost_input + cost_output, 6)
