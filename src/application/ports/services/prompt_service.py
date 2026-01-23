"""
Prompt Service Interface - Contrato para gestión de prompts.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from ....domain.entities.question import QuestionType
from ....domain.entities.section import Section


class PromptService(ABC):
    """
    Interface abstracta para servicios de gestión de prompts.

    Define el contrato para cargar, versionar y construir prompts
    para la generación de preguntas.
    """

    @abstractmethod
    def get_system_prompt(
        self,
        question_type: QuestionType,
        version: Optional[str] = None,
    ) -> str:
        """
        Obtiene el system prompt para un tipo de pregunta.

        Args:
            question_type: Tipo de pregunta
            version: Versión específica (None = última)

        Returns:
            System prompt
        """
        pass

    @abstractmethod
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
            include_context: Si incluir contexto adicional

        Returns:
            User prompt construido
        """
        pass

    @abstractmethod
    def get_available_versions(self, question_type: QuestionType) -> List[str]:
        """
        Lista las versiones disponibles de un prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Lista de versiones disponibles
        """
        pass

    @abstractmethod
    def get_current_version(self, question_type: QuestionType) -> str:
        """
        Obtiene la versión actual/activa de un prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Versión actual
        """
        pass

    @abstractmethod
    def set_current_version(self, question_type: QuestionType, version: str) -> None:
        """
        Establece la versión activa de un prompt.

        Args:
            question_type: Tipo de pregunta
            version: Versión a activar
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_prompt_metadata(self, question_type: QuestionType) -> Dict:
        """
        Obtiene metadata del prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Metadata (versiones, fechas, etc.)
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_prompt_path(self, question_type: QuestionType) -> Path:
        """
        Obtiene la ruta del archivo de prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Ruta al archivo
        """
        pass

    @abstractmethod
    def validate_prompt(self, content: str) -> tuple[bool, List[str]]:
        """
        Valida el contenido de un prompt.

        Args:
            content: Contenido a validar

        Returns:
            Tupla (es_válido, lista_de_errores)
        """
        pass
