"""
Prompt Service Implementation - Implementación del puerto PromptService.
"""

from pathlib import Path
from typing import Dict, List, Optional

from ....application.ports.services import PromptService
from ....domain.entities.section import Section
from ....domain.entities.question import QuestionType
from .loader import PromptLoader
from .builder import PromptBuilder


class PromptServiceImpl(PromptService):
    """
    Implementación concreta del servicio de prompts.

    Gestiona la carga, versionado y construcción de prompts
    para la generación de preguntas.
    """

    # Mapeo de QuestionType a nombre de directorio
    TYPE_TO_DIR = {
        QuestionType.FLASHCARD: "flashcard",
        QuestionType.TRUE_FALSE: "true_false",
        QuestionType.MULTIPLE_CHOICE: "multiple_choice",
        QuestionType.CLOZE: "cloze",
    }

    def __init__(
        self,
        prompts_path: Path,
        include_context: bool = True,
        author: Optional[str] = None,
    ):
        """
        Args:
            prompts_path: Ruta al directorio de prompts
            include_context: (Deprecated) Si incluir contexto
            author: Autor del documento para atribución dinámica
        """
        self._prompts_path = Path(prompts_path)
        self._loader = PromptLoader(self._prompts_path)
        self.author = author
        # PromptBuilder now expects (templates_dir, author)
        self._builder = PromptBuilder(self._prompts_path, self.author)

        # Cache de prompts cargados
        self._cache: Dict[str, str] = {}

    def get_system_prompt(
        self,
        question_type: QuestionType,
        version: Optional[str] = None,
    ) -> str:
        """
        Obtiene el system prompt para un tipo de pregunta.
        Args:
            question_type: Tipo de pregunta
            version: Versión específica (None = activa)
        Returns:
            System prompt
        """
        cache_key = f"{question_type.value}:{version or 'active'}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        dir_name = self.TYPE_TO_DIR.get(question_type, question_type.value)
        loaded = self._loader.load(dir_name, version)

        self._cache[cache_key] = loaded.content
        return loaded.content

    def build_user_prompt(
        self,
        sections: List[Section],
        question_type: QuestionType,
        include_context: bool = True,
    ) -> str:
        """
        Construye el user prompt con las secciones.
        Args:
            sections: Lista de secciones a procesar
            question_type: Tipo de pregunta
            include_context: (Deprecated) Si incluir contexto adicional
        Returns:
            User prompt construido
        """
        # Instantiate builder with correct args
        builder = PromptBuilder(self._prompts_path, self.author)
        return builder.build(sections, question_type)

    def get_available_versions(self, question_type: QuestionType) -> List[str]:
        """
        Lista las versiones disponibles de un prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Lista de versiones disponibles
        """
        dir_name = self.TYPE_TO_DIR.get(question_type, question_type.value)
        return self._loader.list_versions(dir_name)

    def get_current_version(self, question_type: QuestionType) -> str:
        """
        Obtiene la versión actual/activa de un prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Versión actual
        """
        dir_name = self.TYPE_TO_DIR.get(question_type, question_type.value)
        return self._loader.get_active_version(dir_name)

    def set_current_version(
        self,
        question_type: QuestionType,
        version: str,
    ) -> None:
        """
        Establece la versión activa de un prompt.

        Args:
            question_type: Tipo de pregunta
            version: Versión a activar
        """
        dir_name = self.TYPE_TO_DIR.get(question_type, question_type.value)
        self._loader.set_active_version(dir_name, version)

        # Invalidar cache
        cache_key = f"{question_type.value}:active"
        if cache_key in self._cache:
            del self._cache[cache_key]

    def create_version(
        self,
        question_type: QuestionType,
        content: str,
        version: str,
        description: str = "",
    ) -> None:
        """
        Crea una nueva versión de prompt.

        Args:
            question_type: Tipo de pregunta
            content: Contenido del prompt
            version: Número de versión
            description: Descripción de cambios
        """
        dir_name = self.TYPE_TO_DIR.get(question_type, question_type.value)
        self._loader.save_version(
            dir_name,
            version,
            content,
            description,
        )

    def get_prompt_metadata(self, question_type: QuestionType) -> Dict:
        """
        Obtiene metadata del prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Metadata (versiones, fechas, etc.)
        """
        dir_name = self.TYPE_TO_DIR.get(question_type, question_type.value)
        versions = self._loader.list_versions(dir_name)
        active = self._loader.get_active_version(dir_name)

        return {
            "question_type": question_type.value,
            "versions": versions,
            "active_version": active,
            "total_versions": len(versions),
        }

    def estimate_tokens(
        self,
        sections: List[Section],
        question_type: QuestionType,
    ) -> int:
        """
        Estima tokens totales para un prompt.

        Args:
            sections: Secciones a incluir
            question_type: Tipo de pregunta

        Returns:
            Tokens estimados
        """
        # Tokens del system prompt
        system_prompt = self.get_system_prompt(question_type)
        system_tokens = len(system_prompt) // 4

        # Tokens del user prompt
        user_tokens = self._builder.estimate_tokens(sections, question_type)

        return system_tokens + user_tokens

    def get_prompt_path(self, question_type: QuestionType) -> Path:
        """
        Obtiene la ruta del archivo de prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Ruta al archivo
        """
        dir_name = self.TYPE_TO_DIR.get(question_type, question_type.value)
        version = self._loader.get_active_version(dir_name)
        return self._prompts_path / dir_name / f"v{version}.md"

    def validate_prompt(self, content: str) -> tuple[bool, List[str]]:
        """
        Valida el contenido de un prompt.

        Args:
            content: Contenido a validar

        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        errors = []

        # Validar que no esté vacío
        if not content.strip():
            errors.append("El prompt está vacío")
            return False, errors

        # Validar longitud mínima
        if len(content) < 100:
            errors.append("El prompt es muy corto (< 100 caracteres)")

        # Validar que contenga instrucciones JSON
        if "json" not in content.lower():
            errors.append("El prompt debería mencionar formato JSON")

        # Validar placeholders comunes
        required_concepts = ["pregunta", "respuesta"]
        for concept in required_concepts:
            if concept not in content.lower():
                errors.append(f"El prompt debería mencionar '{concept}'")

        return len(errors) == 0, errors

    def clear_cache(self) -> None:
        """Limpia el cache de prompts cargados."""
        self._cache.clear()
