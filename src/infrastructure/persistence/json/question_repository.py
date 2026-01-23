"""
Question Repository JSON - Repositorio de preguntas en JSON.
"""

import json
import glob
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ....application.ports.repositories import QuestionRepository
from ....domain.entities.question import Question, QuestionType, QuestionStatus
from ....domain.value_objects.origin import Origin
from ....domain.value_objects.metadata import Difficulty, QuestionMetadata


class QuestionRepositoryJSON(QuestionRepository):
    """
    Repositorio de preguntas usando JSON como almacenamiento.

    Mantiene compatibilidad con el formato de salida del sistema actual.
    """

    def __init__(self, base_path: Path):
        """
        Args:
            base_path: Ruta base para almacenar archivos JSON
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

        # Cache en memoria
        self._cache: Dict[str, List[Question]] = {}

    def save(self, question: Question) -> None:
        """Guarda una pregunta."""
        doc_id = question.origin.document_id
        questions = self._cache.get(doc_id, [])

        # Buscar si ya existe
        existing_idx = None
        for i, q in enumerate(questions):
            if q.id == question.id:
                existing_idx = i
                break

        if existing_idx is not None:
            questions[existing_idx] = question
        else:
            questions.append(question)

        self._cache[doc_id] = questions

    def save_all(self, questions: List[Question]) -> None:
        """Guarda múltiples preguntas."""
        for question in questions:
            self.save(question)

    def find_by_id(self, question_id: str) -> Optional[Question]:
        """Busca una pregunta por ID."""
        for questions in self._cache.values():
            for q in questions:
                if q.id == question_id:
                    return q
        return None

    def find_all(self, document_id: Optional[str] = None) -> List[Question]:
        """Retorna todas las preguntas de un documento."""
        if document_id:
            return self._cache.get(document_id, [])
        
        all_questions = []
        for questions in self._cache.values():
            all_questions.extend(questions)
        return all_questions

    def find_by_type(self, question_type: QuestionType) -> List[Question]:
        """Retorna preguntas de un tipo específico."""
        all_questions = self.find_all()
        return [q for q in all_questions if q.type == question_type]

    def find_by_status(self, status: QuestionStatus) -> List[Question]:
        """Busca preguntas por estado."""
        all_questions = self.find_all()
        return [q for q in all_questions if q.status == status]

    def find_by_section(self, section_id: int, document_id: str) -> List[Question]:
        """Busca preguntas generadas de una sección específica."""
        questions = self.find_all(document_id)
        return [q for q in questions if q.origin and q.origin.section_id == section_id]

    def find_by_difficulty(self, difficulty: Difficulty) -> List[Question]:
        """Busca preguntas por dificultad."""
        all_questions = self.find_all()
        return [q for q in all_questions if q.metadata and q.metadata.difficulty == difficulty]

    def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[Question]:
        """Busca preguntas por tags."""
        all_questions = self.find_all()
        
        def has_tags(question: Question) -> bool:
            if not question.metadata or not question.metadata.tags:
                return False
            
            tag_set = set(question.metadata.tags)
            if match_all:
                return set(tags).issubset(tag_set)
            else:
                return any(tag in tag_set for tag in tags)

        return [q for q in all_questions if has_tags(q)]

    def find_valid(self, document_id: str) -> List[Question]:
        """Retorna preguntas validadas."""
        questions = self._cache.get(document_id, [])
        return [q for q in questions if q.status == QuestionStatus.VALIDATED]

    def delete(self, question_id: str) -> bool:
        """Elimina una pregunta."""
        for doc_id, questions in self._cache.items():
            original_len = len(questions)
            questions = [q for q in questions if q.id != question_id]

            if len(questions) < original_len:
                self._cache[doc_id] = questions
                return True

        return False

    def delete_all(self, document_id: Optional[str] = None) -> int:
        """Elimina todas las preguntas."""
        if document_id:
            if document_id in self._cache:
                count = len(self._cache[document_id])
                del self._cache[document_id]
                return count
            return 0
        
        count = sum(len(q_list) for q_list in self._cache.values())
        self._cache.clear()
        return count

    def count(self) -> int:
        """Cuenta el total de preguntas."""
        return sum(len(q_list) for q_list in self._cache.values())

    def count_by_type(self) -> dict:
        """Cuenta preguntas agrupadas por tipo."""
        all_questions = self.find_all()
        counts = Counter(q.type.value for q in all_questions)
        return dict(counts)

    def count_by_status(self) -> dict:
        """Cuenta preguntas agrupadas por estado."""
        all_questions = self.find_all()
        counts = Counter(q.status.value for q in all_questions)
        return dict(counts)

    def update_status(self, question_id: str, status: QuestionStatus) -> bool:
        """Actualiza el estado de una pregunta."""
        question = self.find_by_id(question_id)
        if question:
            question.status = status
            self.save(question)
            return True
        return False

    def export_to_json(
        self,
        output_path: Path,
        format: str = "internal",
    ) -> Path:
        """
        Exporta todas las preguntas a JSON.

        Args:
            output_path: Ruta del archivo de salida
            format: Formato de exportación ('internal', 'anki', 'mochi')

        Returns:
            Ruta del archivo generado
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Recopilar todas las preguntas
        all_questions = self.find_all()

        # Formatear según tipo
        if format == "anki":
            data = self._format_for_anki(all_questions)
        elif format == "mochi":
            data = self._format_for_mochi(all_questions)
        else:
            data = self._format_internal(all_questions)

        # Guardar
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        return output_path

    def export_invalid(
        self,
        questions: List[Question],
        output_path: Path,
    ) -> Path:
        """
        Exporta preguntas inválidas para revisión.

        Args:
            questions: Lista de preguntas inválidas
            output_path: Ruta del archivo de salida

        Returns:
            Ruta del archivo generado
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "total_invalid": len(questions),
            },
            "preguntas_invalidas": [
                self._question_to_dict(q) for q in questions
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        return output_path

    def load_from_json(self, json_path: Path) -> List[Question]:
        """
        Importa preguntas desde JSON.

        Args:
            json_path: Ruta del archivo JSON

        Returns:
            Lista de preguntas importadas
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        questions = []

        # Detectar formato
        if "preguntas" in data:
            raw_questions = data["preguntas"]
        elif isinstance(data, list):
            raw_questions = data
        else:
            raw_questions = []

        for raw in raw_questions:
            try:
                question = self._dict_to_question(raw)
                questions.append(question)
            except Exception:
                continue

        # Guardar en cache
        for q in questions:
            self.save(q)

        return questions

    def get_latest_json(self, pattern: str = "preguntas_*.json") -> Optional[Path]:
        """
        Obtiene el JSON más reciente que coincide con el patrón en el base_path.

        Args:
            pattern: Patrón glob para buscar archivos

        Returns:
            Ruta del archivo más reciente o None
        """
        files = glob.glob(str(self._base_path / pattern))
        if not files:
            return None
        
        latest_file = max(files, key=lambda f: Path(f).stat().st_mtime)
        return Path(latest_file)

    def _question_to_dict(self, question: Question) -> Dict:
        """Convierte pregunta a diccionario."""
        return question.to_dict()

    def _content_to_dict(self, question: Question) -> Dict:
        """
        Convierte contenido específico a diccionario.
        """
        return question._content_to_dict()

    def _dict_to_question(self, data: Dict) -> Question:
        """
        Convierte diccionario a pregunta.
        """
        # Parsear tipo - manejar tanto el valor enum como el nombre del miembro para robustez
        tipo_str = data.get("tipo", "flashcards")
        try:
            question_type = QuestionType(tipo_str)
        except ValueError:
            # Fallback a mapeo manual si el string no coincide exactamente con el valor del enum
            mapping = {
                "flashcard": QuestionType.FLASHCARD,
                "true_false": QuestionType.TRUE_FALSE,
                "multiple_choice": QuestionType.MULTIPLE_CHOICE,
                "cloze": QuestionType.CLOZE
            }
            question_type = mapping.get(tipo_str, QuestionType.FLASHCARD)

        # Parsear origin
        origin_data = data.get("origen", {})
        origin = Origin.from_dict(origin_data)

        # Parsear metadata
        metadata_data = data.get("sm2_metadata", data.get("metadata", {}))
        metadata = QuestionMetadata.from_dict(metadata_data)

        # Parsear contenido según tipo
        contenido = data.get("contenido_tipo", {})
        content = None

        if question_type == QuestionType.FLASHCARD:
            from ....domain.entities.question import FlashcardContent
            content = FlashcardContent(
                anverso=contenido.get("anverso", contenido.get("frente", data.get("pregunta", ""))),
                reverso=contenido.get("reverso", data.get("respuesta", "")),
            )
        elif question_type == QuestionType.TRUE_FALSE:
            from ....domain.entities.question import TrueFalseContent
            content = TrueFalseContent(
                pregunta=contenido.get("pregunta", contenido.get("afirmacion", data.get("pregunta", ""))),
                respuesta_correcta=contenido.get("respuesta_correcta", contenido.get("respuesta", True)),
                explicacion=contenido.get("explicacion", contenido.get("justificacion", "")),
            )
        elif question_type == QuestionType.MULTIPLE_CHOICE:
            from ....domain.entities.question import MultipleChoiceContent
            content = MultipleChoiceContent(
                pregunta=contenido.get("pregunta", data.get("pregunta", "")),
                opciones=contenido.get("opciones", []),
                respuesta_correcta=contenido.get("respuesta_correcta", contenido.get("correct_index", 0)),
                explicacion=contenido.get("explicacion", contenido.get("justificacion", "")),
            )
        elif question_type == QuestionType.CLOZE:
            from ....domain.entities.question import ClozeContent
            content = ClozeContent(
                texto_con_espacios=contenido.get("texto_con_espacios", contenido.get("text_with_blanks", "")),
                respuestas_validas=contenido.get("respuestas_validas", contenido.get("valid_answers", [])),
            )

        # Crear pregunta con status restaurado desde JSON
        question = Question(
            id=data.get("id", str(uuid4())[:8]),
            type=question_type,
            question_text=data.get("pregunta", data.get("anverso", "")),
            content=content,
            origin=origin,
            metadata=metadata,
            status=QuestionStatus(data.get("status", "generated")),
            validation_errors=data.get("validation_errors", []),
        )
        
        return question

    def _format_internal(self, questions: List[Question]) -> Dict:
        """
        Formato interno con metadata.
        """
        all_questions = self.find_all()
        return {
            "metadata": {
                "version": "2.0",
                "generated_at": datetime.now().isoformat(),
                "total_preguntas": len(all_questions),
                "preguntas_por_tipo": self.count_by_type(),
            },
            "preguntas": [self._question_to_dict(q) for q in all_questions],
        }

    def _format_for_anki(self, questions: List[Question]) -> List[Dict]:
        """
        Formato compatible con Anki import.
        """
        anki_cards = []

        for q in questions:
            if q.type == QuestionType.FLASHCARD:
                anki_cards.append({
                    "front": q.content.front,
                    "back": q.content.back,
                    "tags": q.metadata.tags if q.metadata else [],
                })
            elif q.type == QuestionType.TRUE_FALSE:
                anki_cards.append({
                    "front": f"Verdadero o Falso: {q.content.statement}",
                    "back": f"{'Verdadero' if q.content.answer else 'Falso'}. {q.content.justification}",
                    "tags": q.metadata.tags if q.metadata else [],
                })

        return anki_cards

    def _format_for_mochi(self, questions: List[Question]) -> Dict:
        """
        Formato compatible con Mochi cards.
        """
        return {
            "version": 2,
            "cards": [
                {
                    "content": f"{q.question_text}\n---\n{self._get_answer_text(q)}",
                    "review-reverse?": False,
                }
                for q in questions
            ],
        }

    def _get_answer_text(self, question: Question) -> str:
        """
        Obtiene texto de respuesta según tipo.
        """
        if question.type == QuestionType.FLASHCARD:
            return question.content.back
        elif question.type == QuestionType.TRUE_FALSE:
            return f"{'Verdadero' if question.content.answer else 'Falso'}"
        elif question.type == QuestionType.MULTIPLE_CHOICE:
            idx = question.content.correct_index
            if 0 <= idx < len(question.content.options):
                return question.content.options[idx]
        return ""

    def clear_cache(self, document_id: Optional[str] = None) -> None:
        """
        Limpia el cache.
        """
        if document_id:
            self._cache.pop(document_id, None)
        else:
            self._cache.clear()