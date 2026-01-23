"""
Question Repository Interface - Contrato para persistencia de preguntas.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ....domain.entities.question import Question, QuestionType, QuestionStatus
from ....domain.value_objects.metadata import Difficulty, QuestionSubtype


class QuestionRepository(ABC):
    """
    Interface abstracta para repositorio de preguntas.

    Define el contrato que deben implementar los adaptadores de
    persistencia de preguntas (JSON, Database, etc.).
    """

    @abstractmethod
    def save(self, question: Question) -> None:
        """
        Guarda una pregunta.

        Args:
            question: Pregunta a guardar
        """
        pass

    @abstractmethod
    def save_all(self, questions: List[Question]) -> None:
        """
        Guarda múltiples preguntas.

        Args:
            questions: Lista de preguntas a guardar
        """
        pass

    @abstractmethod
    def find_by_id(self, question_id: str) -> Optional[Question]:
        """
        Busca una pregunta por ID.

        Args:
            question_id: ID de la pregunta

        Returns:
            Pregunta encontrada o None
        """
        pass

    @abstractmethod
    def find_all(self, document_id: Optional[str] = None) -> List[Question]:
        """
        Obtiene todas las preguntas.

        Args:
            document_id: Filtrar por documento (opcional)

        Returns:
            Lista de preguntas
        """
        pass

    @abstractmethod
    def find_by_type(self, question_type: QuestionType) -> List[Question]:
        """
        Busca preguntas por tipo.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Lista de preguntas de ese tipo
        """
        pass

    @abstractmethod
    def find_by_status(self, status: QuestionStatus) -> List[Question]:
        """
        Busca preguntas por estado.

        Args:
            status: Estado de validación

        Returns:
            Lista de preguntas con ese estado
        """
        pass

    @abstractmethod
    def find_by_section(self, section_id: int, document_id: str) -> List[Question]:
        """
        Busca preguntas generadas de una sección específica.

        Args:
            section_id: ID de la sección
            document_id: ID del documento

        Returns:
            Lista de preguntas de esa sección
        """
        pass

    @abstractmethod
    def find_by_difficulty(self, difficulty: Difficulty) -> List[Question]:
        """
        Busca preguntas por dificultad.

        Args:
            difficulty: Nivel de dificultad

        Returns:
            Lista de preguntas con esa dificultad
        """
        pass

    @abstractmethod
    def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[Question]:
        """
        Busca preguntas por tags.

        Args:
            tags: Lista de tags a buscar
            match_all: Si True, debe tener todos los tags

        Returns:
            Lista de preguntas que coinciden
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Cuenta el total de preguntas.

        Returns:
            Número de preguntas
        """
        pass

    @abstractmethod
    def count_by_type(self) -> dict:
        """
        Cuenta preguntas agrupadas por tipo.

        Returns:
            Diccionario {tipo: count}
        """
        pass

    @abstractmethod
    def count_by_status(self) -> dict:
        """
        Cuenta preguntas agrupadas por estado.

        Returns:
            Diccionario {status: count}
        """
        pass

    @abstractmethod
    def delete(self, question_id: str) -> bool:
        """
        Elimina una pregunta.

        Args:
            question_id: ID de la pregunta

        Returns:
            True si se eliminó
        """
        pass

    @abstractmethod
    def delete_all(self, document_id: Optional[str] = None) -> int:
        """
        Elimina todas las preguntas.

        Args:
            document_id: Filtrar por documento (opcional)

        Returns:
            Número de preguntas eliminadas
        """
        pass

    @abstractmethod
    def update_status(self, question_id: str, status: QuestionStatus) -> bool:
        """
        Actualiza el estado de una pregunta.

        Args:
            question_id: ID de la pregunta
            status: Nuevo estado

        Returns:
            True si se actualizó
        """
        pass

    @abstractmethod
    def export_to_json(self, output_path: Path, format: str = "internal") -> Path:
        """
        Exporta preguntas a JSON.

        Args:
            output_path: Ruta de salida
            format: Formato ("internal", "lexquest", "moodle")

        Returns:
            Ruta del archivo generado
        """
        pass

    @abstractmethod
    def load_from_json(self, json_path: Path) -> List[Question]:
        """
        Carga preguntas desde JSON.

        Args:
            json_path: Ruta del archivo JSON

        Returns:
            Lista de preguntas cargadas
        """
        pass

    @abstractmethod
    def get_latest_json(self, pattern: str = "preguntas_*.json") -> Optional[Path]:
        """
        Obtiene el JSON más reciente que coincide con el patrón.

        Args:
            pattern: Patrón glob para buscar archivos

        Returns:
            Ruta del archivo más reciente o None
        """
        pass
