"""
Experiment Repository JSON - Repositorio de experimentos en JSON.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid


class ExperimentRepositoryJSON:
    """
    Repositorio de experimentos usando JSON como almacenamiento.

    Registra cada ejecución del pipeline para reproducibilidad
    y análisis de rendimiento.
    """

    EXPERIMENTS_FILE = "experiments.json"

    def __init__(self, base_path: Path):
        """
        Args:
            base_path: Ruta base para almacenar archivos
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

        self._experiments_path = self._base_path / self.EXPERIMENTS_FILE

        # Cargar experimentos existentes
        self._experiments: Dict[str, Dict] = self._load_experiments()

    def create(
        self,
        llm_provider: str,
        model: str,
        batch_size: int,
        question_type: str,
        prompt_version: str,
        source_hash: str,
        tags: Optional[Dict] = None,
    ) -> str:
        """
        Crea un nuevo experimento.

        Args:
            llm_provider: Proveedor de LLM usado
            model: Modelo específico
            batch_size: Tamaño de batch
            question_type: Tipo de pregunta
            prompt_version: Versión del prompt
            source_hash: Hash del documento fuente
            tags: Tags adicionales

        Returns:
            ID del experimento creado
        """
        experiment_id = str(uuid.uuid4())[:8]

        experiment = {
            "id": experiment_id,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "config": {
                "llm_provider": llm_provider,
                "model": model,
                "batch_size": batch_size,
                "question_type": question_type,
                "prompt_version": prompt_version,
                "source_hash": source_hash,
            },
            "tags": tags or {},
            "results": {
                "total_questions": 0,
                "valid_questions": 0,
                "execution_time_seconds": 0,
                "total_cost_usd": 0,
                "tokens_used": 0,
            },
        }

        self._experiments[experiment_id] = experiment
        self._save_experiments()

        return experiment_id

    def update_results(
        self,
        experiment_id: str,
        total_questions: int,
        valid_questions: int,
        execution_time_seconds: float,
        total_cost_usd: float,
        tokens_used: int,
    ) -> None:
        """
        Actualiza los resultados de un experimento.

        Args:
            experiment_id: ID del experimento
            total_questions: Total de preguntas generadas
            valid_questions: Preguntas válidas
            execution_time_seconds: Tiempo de ejecución
            total_cost_usd: Costo total
            tokens_used: Tokens usados
        """
        if experiment_id not in self._experiments:
            return

        self._experiments[experiment_id]["results"] = {
            "total_questions": total_questions,
            "valid_questions": valid_questions,
            "execution_time_seconds": execution_time_seconds,
            "total_cost_usd": total_cost_usd,
            "tokens_used": tokens_used,
        }

        self._save_experiments()

    def complete(self, experiment_id: str) -> None:
        """Marca un experimento como completado."""
        if experiment_id in self._experiments:
            self._experiments[experiment_id]["status"] = "completed"
            self._experiments[experiment_id]["completed_at"] = datetime.now().isoformat()
            self._save_experiments()

    def fail(self, experiment_id: str, error_message: str) -> None:
        """Marca un experimento como fallido."""
        if experiment_id in self._experiments:
            self._experiments[experiment_id]["status"] = "failed"
            self._experiments[experiment_id]["completed_at"] = datetime.now().isoformat()
            self._experiments[experiment_id]["error"] = error_message
            self._save_experiments()

    def find_by_id(self, experiment_id: str) -> Optional[Dict]:
        """Busca un experimento por ID."""
        return self._experiments.get(experiment_id)

    def find_all(self) -> List[Dict]:
        """Retorna todos los experimentos."""
        return list(self._experiments.values())

    def find_by_status(self, status: str) -> List[Dict]:
        """Busca experimentos por estado."""
        return [
            exp for exp in self._experiments.values()
            if exp["status"] == status
        ]

    def find_by_provider(self, provider: str) -> List[Dict]:
        """Busca experimentos por proveedor de LLM."""
        return [
            exp for exp in self._experiments.values()
            if exp["config"]["llm_provider"] == provider
        ]

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de todos los experimentos."""
        experiments = list(self._experiments.values())

        if not experiments:
            return {
                "total_experiments": 0,
                "completed": 0,
                "failed": 0,
                "running": 0,
            }

        completed = [e for e in experiments if e["status"] == "completed"]

        return {
            "total_experiments": len(experiments),
            "completed": len(completed),
            "failed": len([e for e in experiments if e["status"] == "failed"]),
            "running": len([e for e in experiments if e["status"] == "running"]),
            "total_questions_generated": sum(
                e["results"]["total_questions"] for e in completed
            ),
            "total_cost_usd": sum(
                e["results"]["total_cost_usd"] for e in completed
            ),
            "average_execution_time": (
                sum(e["results"]["execution_time_seconds"] for e in completed) / len(completed)
                if completed else 0
            ),
        }

    def compare_experiments(
        self,
        experiment_ids: List[str],
    ) -> Dict:
        """
        Compara múltiples experimentos.

        Args:
            experiment_ids: Lista de IDs a comparar

        Returns:
            Comparación de experimentos
        """
        experiments = [
            self._experiments.get(eid)
            for eid in experiment_ids
            if eid in self._experiments
        ]

        if not experiments:
            return {}

        return {
            "experiments": [
                {
                    "id": e["id"],
                    "provider": e["config"]["llm_provider"],
                    "model": e["config"]["model"],
                    "questions": e["results"]["total_questions"],
                    "valid": e["results"]["valid_questions"],
                    "cost": e["results"]["total_cost_usd"],
                    "time": e["results"]["execution_time_seconds"],
                }
                for e in experiments
            ],
        }

    def delete(self, experiment_id: str) -> bool:
        """Elimina un experimento."""
        if experiment_id in self._experiments:
            del self._experiments[experiment_id]
            self._save_experiments()
            return True
        return False

    def _load_experiments(self) -> Dict[str, Dict]:
        """Carga experimentos desde archivo."""
        if self._experiments_path.exists():
            try:
                with open(self._experiments_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("experiments", {})
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_experiments(self) -> None:
        """Guarda experimentos a archivo."""
        data = {
            "version": "2.0",
            "updated_at": datetime.now().isoformat(),
            "experiments": self._experiments,
        }

        with open(self._experiments_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
