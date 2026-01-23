"""
Experiment Repository Interface - Contrato para tracking de experimentos.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExperimentRepository(ABC):
    """
    Interface abstracta para repositorio de experimentos.

    Define el contrato para tracking de experimentos de generación,
    permitiendo reproducibilidad y comparación de resultados.
    """

    @abstractmethod
    def create(
        self,
        llm_provider: str,
        model: str,
        batch_size: int,
        question_type: str,
        prompt_version: str,
        source_hash: str,
        tags: Optional[Dict[str, str]] = None,
        notes: str = "",
    ) -> str:
        """
        Crea un nuevo experimento.

        Args:
            llm_provider: Proveedor de LLM usado
            model: Modelo específico
            batch_size: Tamaño de batch
            question_type: Tipo de preguntas generadas
            prompt_version: Versión del prompt
            source_hash: Hash del archivo fuente
            tags: Tags para categorización
            notes: Notas adicionales

        Returns:
            ID del experimento creado
        """
        pass

    @abstractmethod
    def update_results(
        self,
        experiment_id: str,
        total_questions: int,
        valid_questions: int,
        execution_time_seconds: float,
        total_cost_usd: float,
        tokens_used: int,
        errors: Optional[List[str]] = None,
    ) -> None:
        """
        Actualiza resultados de un experimento.

        Args:
            experiment_id: ID del experimento
            total_questions: Total de preguntas generadas
            valid_questions: Preguntas válidas
            execution_time_seconds: Tiempo de ejecución
            total_cost_usd: Costo total en USD
            tokens_used: Tokens utilizados
            errors: Lista de errores
        """
        pass

    @abstractmethod
    def complete(self, experiment_id: str) -> None:
        """
        Marca un experimento como completado.

        Args:
            experiment_id: ID del experimento
        """
        pass

    @abstractmethod
    def fail(self, experiment_id: str, error_message: str) -> None:
        """
        Marca un experimento como fallido.

        Args:
            experiment_id: ID del experimento
            error_message: Mensaje de error
        """
        pass

    @abstractmethod
    def find_by_id(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca un experimento por ID.

        Args:
            experiment_id: ID del experimento

        Returns:
            Datos del experimento o None
        """
        pass

    @abstractmethod
    def find_all(
        self,
        llm_provider: Optional[str] = None,
        question_type: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lista experimentos con filtros opcionales.

        Args:
            llm_provider: Filtrar por proveedor
            question_type: Filtrar por tipo de pregunta
            tags: Filtrar por tags
            start_date: Fecha inicial
            end_date: Fecha final

        Returns:
            Lista de experimentos
        """
        pass

    @abstractmethod
    def compare(self, experiment_ids: List[str]) -> Dict[str, Any]:
        """
        Compara múltiples experimentos.

        Args:
            experiment_ids: IDs de experimentos a comparar

        Returns:
            Diccionario con comparación de métricas
        """
        pass

    @abstractmethod
    def get_best(
        self,
        metric: str = "validation_rate",
        question_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los mejores experimentos por métrica.

        Args:
            metric: Métrica para ordenar (validation_rate, questions_per_minute, cost_per_question)
            question_type: Filtrar por tipo de pregunta
            limit: Número máximo de resultados

        Returns:
            Lista de mejores experimentos
        """
        pass

    @abstractmethod
    def delete(self, experiment_id: str) -> bool:
        """
        Elimina un experimento.

        Args:
            experiment_id: ID del experimento

        Returns:
            True si se eliminó
        """
        pass

    @abstractmethod
    def export_to_csv(self, output_path: Path) -> Path:
        """
        Exporta experimentos a CSV para análisis.

        Args:
            output_path: Ruta de salida

        Returns:
            Ruta del archivo generado
        """
        pass

    @abstractmethod
    def add_note(self, experiment_id: str, note: str) -> None:
        """
        Agrega una nota a un experimento.

        Args:
            experiment_id: ID del experimento
            note: Nota a agregar
        """
        pass

    @abstractmethod
    def add_tag(self, experiment_id: str, key: str, value: str) -> None:
        """
        Agrega un tag a un experimento.

        Args:
            experiment_id: ID del experimento
            key: Clave del tag
            value: Valor del tag
        """
        pass
