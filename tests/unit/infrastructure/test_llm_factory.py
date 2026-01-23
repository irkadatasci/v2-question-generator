"""Tests para LLM Factory."""

import pytest
from src.infrastructure.llm import LLMFactory, LLMProvider, LLMConfig
from src.infrastructure.llm.backends import (
    KimiBackend,
    GroqBackend,
    OpenAIBackend,
    OllamaBackend,
)


class TestLLMFactory:
    """Tests para LLMFactory."""

    def test_create_kimi_backend(self):
        """Debe crear backend de Kimi."""
        config = LLMConfig(
            api_key="test_key",
            model="moonshot-v1-8k",
        )

        backend = LLMFactory.create(LLMProvider.KIMI, config)

        assert isinstance(backend, KimiBackend)
        assert backend.provider_name == "kimi"
        assert backend.model_name == "moonshot-v1-8k"

    def test_create_groq_backend(self):
        """Debe crear backend de Groq."""
        config = LLMConfig(
            api_key="test_key",
            model="llama-3.3-70b-versatile",
        )

        backend = LLMFactory.create(LLMProvider.GROQ, config)

        assert isinstance(backend, GroqBackend)
        assert backend.provider_name == "groq"

    def test_create_openai_backend(self):
        """Debe crear backend de OpenAI."""
        config = LLMConfig(
            api_key="test_key",
            model="gpt-4o-mini",
        )

        backend = LLMFactory.create(LLMProvider.OPENAI, config)

        assert isinstance(backend, OpenAIBackend)
        assert backend.provider_name == "openai"

    def test_create_ollama_backend(self):
        """Debe crear backend de Ollama."""
        config = LLMConfig(
            api_key="",  # Ollama no requiere API key
            model="llama3.2",
        )

        backend = LLMFactory.create(LLMProvider.OLLAMA, config)

        assert isinstance(backend, OllamaBackend)
        assert backend.provider_name == "ollama"

    def test_create_from_string(self):
        """Debe crear backend desde string."""
        config = LLMConfig(api_key="test_key")

        backend = LLMFactory.create_from_string("kimi", config)

        assert isinstance(backend, KimiBackend)

    def test_create_invalid_provider_raises_error(self):
        """Debe lanzar error con proveedor inválido."""
        config = LLMConfig(api_key="test_key")

        with pytest.raises(ValueError, match="no reconocido"):
            LLMFactory.create_from_string("invalid_provider", config)

    def test_get_available_providers(self):
        """Debe listar proveedores disponibles."""
        providers = LLMFactory.get_available_providers()

        assert "kimi" in providers
        assert "groq" in providers
        assert "openai" in providers
        assert "ollama" in providers

    def test_get_default_model(self):
        """Debe obtener modelo por defecto."""
        kimi_model = LLMFactory.get_default_model(LLMProvider.KIMI)
        groq_model = LLMFactory.get_default_model(LLMProvider.GROQ)

        assert kimi_model == "moonshot-v1-128k"
        assert groq_model == "llama-3.3-70b-versatile"

    def test_get_available_models(self):
        """Debe listar modelos disponibles por proveedor."""
        kimi_models = LLMFactory.get_available_models(LLMProvider.KIMI)
        openai_models = LLMFactory.get_available_models(LLMProvider.OPENAI)

        assert "moonshot-v1-8k" in kimi_models
        assert "moonshot-v1-32k" in kimi_models
        assert "moonshot-v1-128k" in kimi_models

        assert "gpt-4o" in openai_models
        assert "gpt-4o-mini" in openai_models
