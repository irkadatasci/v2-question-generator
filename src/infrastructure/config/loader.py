"""
Config Loader - Carga configuración desde múltiples fuentes.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from .settings import (
    Settings,
    LLMSettings,
    PathSettings,
    ClassificationSettings,
    GenerationSettings,
)


class ConfigLoader:
    """
    Carga configuración desde múltiples fuentes.

    Prioridad (mayor a menor):
    1. Variables de entorno
    2. Archivo de configuración
    3. Valores por defecto

    Soporta archivos JSON y .env.
    """

    # Variables de entorno para LLM
    ENV_VARS = {
        "kimi": "MOONSHOT_API_KEY",
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "ollama": "OLLAMA_HOST",
        "ollama_cloud": "OLLAMA_CLOUD_API_KEY",
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: Ruta al archivo de configuración
        """
        self._config_path = config_path
        self._env_loaded = False

    def load(self) -> Settings:
        """
        Carga la configuración completa.

        Returns:
            Settings configurado
        """
        # Cargar .env si existe
        self._load_dotenv()

        # Cargar desde archivo si existe
        file_config = {}
        if self._config_path and self._config_path.exists():
            file_config = self._load_from_file(self._config_path)

        # Construir settings
        settings = self._build_settings(file_config)

        return settings

    def load_from_dict(self, config: Dict) -> Settings:
        """
        Carga configuración desde un diccionario.

        Args:
            config: Diccionario de configuración

        Returns:
            Settings configurado
        """
        self._load_dotenv()
        return self._build_settings(config)

    def _load_dotenv(self) -> None:
        """Carga variables desde .env si existe."""
        if self._env_loaded:
            return

        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=True)

        self._env_loaded = True

    def _load_from_file(self, path: Path) -> Dict:
        """Carga configuración desde archivo JSON."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _build_settings(self, config: Dict) -> Settings:
        """Construye Settings desde diccionario y env."""
        # LLM providers
        llm_providers = {}
        llm_config = config.get("llm", {})

        for provider in ["kimi", "groq", "openai", "ollama", "ollama_cloud"]:
            provider_config = llm_config.get(provider, {})

            # Obtener API key desde env o config
            env_var = self.ENV_VARS.get(provider, "")
            api_key = os.getenv(env_var, provider_config.get("api_key", ""))

            llm_providers[provider] = LLMSettings(
                provider=provider,
                api_key=api_key,
                model=provider_config.get("model", ""),
                base_url=provider_config.get("base_url"),
                temperature=provider_config.get("temperature", 0.7),
                max_tokens=provider_config.get("max_tokens", 4096),
                timeout=provider_config.get("timeout", 120),
                retry_attempts=provider_config.get("retry_attempts", 3),
                context_caching=provider_config.get("context_caching", False),
            )

        # Paths
        paths_config = config.get("paths", {})
        paths = PathSettings(
            base_dir=Path(paths_config.get("base_dir", Path.cwd())),
            prompts_dir=Path(paths_config.get("prompts_dir", "prompts")),
            output_dir=Path(paths_config.get("output_dir", "datos/procesadas")),
            intermediate_dir=Path(paths_config.get("intermediate_dir", "datos/intermediate")),
            experiments_dir=Path(paths_config.get("experiments_dir", "datos/experiments")),
        )

        # Classification
        class_config = config.get("classification", {})
        classification = ClassificationSettings(
            threshold_relevant=class_config.get("threshold_relevant", 0.7),
            threshold_review=class_config.get("threshold_review", 0.5),
            auto_conserve_length=class_config.get("auto_conserve_length", 300),
            weight_as=class_config.get("weight_as", 0.30),
            weight_rj=class_config.get("weight_rj", 0.40),
            weight_dc=class_config.get("weight_dc", 0.20),
            weight_cc=class_config.get("weight_cc", 0.10),
        )

        # Generation
        gen_config = config.get("generation", {})
        generation = GenerationSettings(
            default_batch_size=gen_config.get("default_batch_size", 5),
            auto_adjust_batch_size=gen_config.get("auto_adjust_batch_size", True),
            only_relevant_sections=gen_config.get("only_relevant_sections", True),
            default_question_type=gen_config.get("default_question_type", "flashcard"),
            validation_level=gen_config.get("validation_level", "moderate"),
            auto_fix_questions=gen_config.get("auto_fix_questions", True),
        )

        return Settings(
            llm_providers=llm_providers,
            default_llm_provider=config.get("default_llm_provider", "kimi"),
            paths=paths,
            classification=classification,
            generation=generation,
            debug=config.get("debug", False),
            log_level=config.get("log_level", "INFO"),
            log_file=Path(config["log_file"]) if config.get("log_file") else None,
        )

    def save(self, settings: Settings, output_path: Path) -> None:
        """
        Guarda la configuración actual a un archivo.

        Args:
            settings: Settings a guardar
            output_path: Ruta de salida
        """
        config = {
            "default_llm_provider": settings.default_llm_provider,
            "llm": {
                name: {
                    "model": s.model,
                    "base_url": s.base_url,
                    "temperature": s.temperature,
                    "max_tokens": s.max_tokens,
                    "timeout": s.timeout,
                    # NO guardar API keys
                }
                for name, s in settings.llm_providers.items()
            },
            "paths": {
                "prompts_dir": str(settings.paths.prompts_dir),
                "output_dir": str(settings.paths.output_dir),
                "intermediate_dir": str(settings.paths.intermediate_dir),
                "experiments_dir": str(settings.paths.experiments_dir),
            },
            "classification": {
                "threshold_relevant": settings.classification.threshold_relevant,
                "threshold_review": settings.classification.threshold_review,
                "auto_conserve_length": settings.classification.auto_conserve_length,
            },
            "generation": {
                "default_batch_size": settings.generation.default_batch_size,
                "auto_adjust_batch_size": settings.generation.auto_adjust_batch_size,
                "only_relevant_sections": settings.generation.only_relevant_sections,
                "default_question_type": settings.generation.default_question_type,
                "validation_level": settings.generation.validation_level,
                "auto_fix_questions": settings.generation.auto_fix_questions,
            },
            "debug": settings.debug,
            "log_level": settings.log_level,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    @staticmethod
    def create_template(output_path: Path) -> None:
        """
        Crea un archivo de configuración de ejemplo.

        Args:
            output_path: Ruta donde crear el template
        """
        template = {
            "default_llm_provider": "kimi",
            "llm": {
                "kimi": {
                    "model": "moonshot-v1-128k",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                },
                "groq": {
                    "model": "llama-3.3-70b-versatile",
                    "temperature": 0.7,
                },
                "openai": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                },
                "ollama": {
                    "model": "llama3.2",
                    "base_url": "http://localhost:11434",
                },
                "ollama_cloud": {
                    "model": "ministral-3:14b-cloud",
                    "base_url": "https://ollama.com/api",
                },
            },
            "paths": {
                "prompts_dir": "prompts",
                "output_dir": "datos/procesadas",
                "intermediate_dir": "datos/intermediate",
                "experiments_dir": "datos/experiments",
            },
            "classification": {
                "threshold_relevant": 0.7,
                "threshold_review": 0.5,
                "auto_conserve_length": 300,
            },
            "generation": {
                "default_batch_size": 5,
                "auto_adjust_batch_size": True,
                "default_question_type": "flashcard",
                "validation_level": "moderate",
            },
            "debug": False,
            "log_level": "INFO",
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
