"""
Settings - Modelos de configuración con validación.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import os


@dataclass
class LLMSettings:
    """Configuración de un proveedor de LLM."""
    provider: str
    api_key: str = ""
    model: str = ""
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    retry_attempts: int = 3
    context_caching: bool = False

    def __post_init__(self):
        """Valida y carga API key desde env si está vacía."""
        if not self.api_key:
            env_var = f"{self.provider.upper()}_API_KEY"
            self.api_key = os.getenv(env_var, "")

    def is_configured(self) -> bool:
        """Verifica si el proveedor está configurado."""
        # Ollama no requiere API key
        if self.provider == "ollama":
            return True
        return bool(self.api_key)


@dataclass
class PathSettings:
    """Configuración de rutas del sistema."""
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    prompts_dir: Path = field(default_factory=lambda: Path("prompts"))
    output_dir: Path = field(default_factory=lambda: Path("datos/procesadas"))
    intermediate_dir: Path = field(default_factory=lambda: Path("datos/intermediate"))
    experiments_dir: Path = field(default_factory=lambda: Path("datos/experiments"))

    def __post_init__(self):
        """Resuelve rutas relativas a base_dir."""
        self.prompts_dir = self._resolve(self.prompts_dir)
        self.output_dir = self._resolve(self.output_dir)
        self.intermediate_dir = self._resolve(self.intermediate_dir)
        self.experiments_dir = self._resolve(self.experiments_dir)

    def _resolve(self, path: Path) -> Path:
        """Resuelve una ruta relativa a base_dir."""
        if path.is_absolute():
            return path
        return self.base_dir / path

    def ensure_dirs(self) -> None:
        """Crea los directorios si no existen."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.intermediate_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class ClassificationSettings:
    """Configuración de clasificación semántica."""
    threshold_relevant: float = 0.7
    threshold_review: float = 0.5
    auto_conserve_length: int = 300

    # Pesos de métricas
    weight_as: float = 0.30  # Aptitud Semántica
    weight_rj: float = 0.40  # Relevancia Jurídica
    weight_dc: float = 0.20  # Densidad Conceptual
    weight_cc: float = 0.10  # Claridad Contextual


@dataclass
class GenerationSettings:
    """Configuración de generación de preguntas."""
    default_batch_size: int = 5
    auto_adjust_batch_size: bool = True
    only_relevant_sections: bool = True
    default_question_type: str = "flashcard"

    # Validación
    validation_level: str = "moderate"  # strict, moderate, lenient
    auto_fix_questions: bool = True


@dataclass
class Settings:
    """Configuración principal de la aplicación."""

    # LLM providers (puede haber múltiples configurados)
    llm_providers: Dict[str, LLMSettings] = field(default_factory=dict)
    default_llm_provider: str = "kimi"

    # Rutas
    paths: PathSettings = field(default_factory=PathSettings)

    # Clasificación
    classification: ClassificationSettings = field(default_factory=ClassificationSettings)

    # Generación
    generation: GenerationSettings = field(default_factory=GenerationSettings)

    # Debug y logging
    debug: bool = False
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    def get_llm_settings(self, provider: Optional[str] = None) -> LLMSettings:
        """
        Obtiene configuración de un proveedor de LLM.

        Args:
            provider: Nombre del proveedor (None = default)

        Returns:
            LLMSettings del proveedor
        """
        provider = provider or self.default_llm_provider

        if provider in self.llm_providers:
            return self.llm_providers[provider]

        # Crear configuración por defecto
        return LLMSettings(provider=provider)

    def get_configured_providers(self) -> List[str]:
        """Lista proveedores configurados (con API key)."""
        return [
            name for name, settings in self.llm_providers.items()
            if settings.is_configured()
        ]

    def validate(self) -> tuple[bool, List[str]]:
        """
        Valida la configuración.

        Returns:
            Tupla (es_válida, lista_de_errores)
        """
        errors = []

        # Verificar que hay al menos un proveedor configurado
        configured = self.get_configured_providers()
        if not configured:
            errors.append("No hay proveedores de LLM configurados")

        # Verificar proveedor por defecto
        if self.default_llm_provider not in self.llm_providers:
            if self.default_llm_provider not in ["kimi", "groq", "openai", "ollama", "ollama_cloud"]:
                errors.append(f"Proveedor por defecto inválido: {self.default_llm_provider}")

        # Verificar directorios de prompts
        if not self.paths.prompts_dir.exists():
            errors.append(f"Directorio de prompts no existe: {self.paths.prompts_dir}")

        # Verificar umbrales de clasificación
        if not 0 <= self.classification.threshold_review <= self.classification.threshold_relevant <= 1:
            errors.append("Umbrales de clasificación inválidos")

        return len(errors) == 0, errors

    def to_dict(self) -> Dict:
        """Convierte a diccionario (sin API keys)."""
        return {
            "default_llm_provider": self.default_llm_provider,
            "configured_providers": self.get_configured_providers(),
            "paths": {
                "prompts": str(self.paths.prompts_dir),
                "output": str(self.paths.output_dir),
            },
            "classification": {
                "threshold_relevant": self.classification.threshold_relevant,
                "threshold_review": self.classification.threshold_review,
            },
            "generation": {
                "batch_size": self.generation.default_batch_size,
                "question_type": self.generation.default_question_type,
            },
            "debug": self.debug,
        }
