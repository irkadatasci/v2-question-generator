"""
Validate Questions Use Case - Valida preguntas generadas.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ...domain.entities.question import Question, QuestionStatus
from ..ports.repositories import QuestionRepository


@dataclass
class ValidateQuestionsRequest:
    """Request para validar preguntas."""
    document_id: str
    validation_level: str = "strict"  # "strict", "moderate", "lenient"
    auto_fix: bool = False
    export_invalid: bool = True


@dataclass
class ValidationIssue:
    """Representa un problema de validación."""
    question_id: str
    field: str
    issue_type: str
    message: str
    severity: str  # "error", "warning"
    auto_fixable: bool = False


@dataclass
class ValidateQuestionsResult:
    """Resultado de la validación."""
    success: bool
    total_questions: int = 0
    valid_questions: int = 0
    invalid_questions: int = 0
    fixed_questions: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    output_invalid_path: Optional[Path] = None
    error_message: str = ""
    execution_time_seconds: float = 0.0


class ValidateQuestionsUseCase:
    """
    Caso de uso: Validar preguntas generadas.

    Aplica validaciones de estructura, contenido y calidad
    a las preguntas generadas por el LLM.

    Etapa 4 del pipeline.
    """

    # Configuración de validaciones por nivel
    VALIDATION_RULES = {
        "strict": {
            "min_question_length": 20,
            "min_answer_length": 10,
            "require_justification": True,
            "check_duplicates": True,
            "check_completeness": True,
        },
        "moderate": {
            "min_question_length": 15,
            "min_answer_length": 5,
            "require_justification": False,
            "check_duplicates": True,
            "check_completeness": True,
        },
        "lenient": {
            "min_question_length": 10,
            "min_answer_length": 3,
            "require_justification": False,
            "check_duplicates": False,
            "check_completeness": False,
        },
    }

    def __init__(self, question_repository: QuestionRepository):
        """
        Args:
            question_repository: Repositorio de preguntas
        """
        self._questions = question_repository

    def execute(self, request: ValidateQuestionsRequest) -> ValidateQuestionsResult:
        """
        Ejecuta la validación de preguntas.

        Args:
            request: Request con parámetros de validación

        Returns:
            ValidateQuestionsResult con el resultado
        """
        start_time = datetime.now()

        try:
            # 1. Obtener preguntas a validar
            questions = self._questions.find_all(request.document_id)

            if not questions:
                return ValidateQuestionsResult(
                    success=False,
                    error_message=f"No se encontraron preguntas para documento {request.document_id}",
                )

            # 2. Obtener reglas según nivel
            rules = self.VALIDATION_RULES.get(
                request.validation_level,
                self.VALIDATION_RULES["moderate"]
            )

            # 3. Validar cada pregunta
            all_issues: List[ValidationIssue] = []
            issues_by_type: Dict[str, int] = {}
            valid_count = 0
            invalid_count = 0
            fixed_count = 0

            for question in questions:
                issues = self._validate_question(question, rules)

                if issues:
                    # Intentar auto-fix si está habilitado
                    if request.auto_fix:
                        fixed = self._try_auto_fix(question, issues)
                        if fixed:
                            fixed_count += 1
                            # Re-validar después del fix
                            issues = self._validate_question(question, rules)

                    if issues:
                        # Aún tiene problemas
                        question.mark_invalid([i.message for i in issues])
                        invalid_count += 1
                        all_issues.extend(issues)

                        for issue in issues:
                            issues_by_type[issue.issue_type] = (
                                issues_by_type.get(issue.issue_type, 0) + 1
                            )
                    else:
                        question.mark_validated()
                        valid_count += 1
                else:
                    question.mark_validated()
                    valid_count += 1

            # 4. Guardar preguntas actualizadas
            self._questions.save_all(questions)

            # 5. Exportar inválidas si se requiere
            output_invalid = None
            if request.export_invalid and invalid_count > 0:
                invalid_questions = [
                    q for q in questions
                    if q.status == QuestionStatus.INVALID
                ]
                output_invalid = self._questions.export_invalid(
                    questions=invalid_questions,
                    output_path=Path(f"datos/invalid/preguntas_invalidas_{request.document_id}.json"),
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return ValidateQuestionsResult(
                success=True,
                total_questions=len(questions),
                valid_questions=valid_count,
                invalid_questions=invalid_count,
                fixed_questions=fixed_count,
                issues=all_issues,
                issues_by_type=issues_by_type,
                output_invalid_path=output_invalid,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            return ValidateQuestionsResult(
                success=False,
                error_message=f"Error en validación: {e}",
            )

    def _validate_question(
        self,
        question: Question,
        rules: Dict,
    ) -> List[ValidationIssue]:
        """
        Valida una pregunta individual.

        Args:
            question: Pregunta a validar
            rules: Reglas de validación

        Returns:
            Lista de problemas encontrados
        """
        issues = []

        # 1. Validar longitud de pregunta
        if len(question.question_text) < rules["min_question_length"]:
            issues.append(ValidationIssue(
                question_id=question.id,
                field="question_text",
                issue_type="too_short",
                message=f"Pregunta muy corta ({len(question.question_text)} caracteres)",
                severity="error",
                auto_fixable=False,
            ))

        # 2. Validar según tipo de pregunta
        type_issues = self._validate_by_type(question, rules)
        issues.extend(type_issues)

        # 3. Validar origen
        if not question.origin.section_id:
            issues.append(ValidationIssue(
                question_id=question.id,
                field="origin",
                issue_type="missing_origin",
                message="Falta referencia a sección de origen",
                severity="warning",
                auto_fixable=False,
            ))

        # 4. Validar contenido vacío
        if not question.question_text.strip():
            issues.append(ValidationIssue(
                question_id=question.id,
                field="question_text",
                issue_type="empty_content",
                message="Pregunta vacía",
                severity="error",
                auto_fixable=False,
            ))

        # 5. Validar caracteres problemáticos
        problematic_chars = self._check_problematic_chars(question.question_text)
        if problematic_chars:
            issues.append(ValidationIssue(
                question_id=question.id,
                field="question_text",
                issue_type="problematic_chars",
                message=f"Caracteres problemáticos: {problematic_chars}",
                severity="warning",
                auto_fixable=True,
            ))

        return issues

    def _validate_by_type(
        self,
        question: Question,
        rules: Dict,
    ) -> List[ValidationIssue]:
        """Validaciones específicas por tipo de pregunta."""
        issues = []
        content = question.content

        if question.type.value == "flashcard":
            # Validar flashcard
            if not content.front.strip():
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.front",
                    issue_type="empty_front",
                    message="Frente de flashcard vacío",
                    severity="error",
                    auto_fixable=False,
                ))
            if not content.back.strip():
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.back",
                    issue_type="empty_back",
                    message="Reverso de flashcard vacío",
                    severity="error",
                    auto_fixable=False,
                ))

        elif question.type.value == "true_false":
            # Validar verdadero/falso
            if rules["require_justification"] and not content.justification:
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.justification",
                    issue_type="missing_justification",
                    message="Falta justificación",
                    severity="warning",
                    auto_fixable=False,
                ))

        elif question.type.value == "multiple_choice":
            # Validar opción múltiple
            if len(content.options) < 3:
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.options",
                    issue_type="insufficient_options",
                    message=f"Muy pocas opciones ({len(content.options)})",
                    severity="error",
                    auto_fixable=False,
                ))
            if content.correct_index >= len(content.options):
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.correct_index",
                    issue_type="invalid_correct_index",
                    message="Índice de respuesta correcta inválido",
                    severity="error",
                    auto_fixable=False,
                ))
            # Verificar opciones duplicadas
            if len(content.options) != len(set(content.options)):
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.options",
                    issue_type="duplicate_options",
                    message="Opciones duplicadas",
                    severity="error",
                    auto_fixable=False,
                ))

        elif question.type.value == "cloze":
            # Validar cloze
            if "{{c1::" not in content.text_with_blanks and "_____" not in content.text_with_blanks:
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.text_with_blanks",
                    issue_type="no_blanks",
                    message="No se encontraron espacios en blanco",
                    severity="error",
                    auto_fixable=False,
                ))
            if not content.valid_answers:
                issues.append(ValidationIssue(
                    question_id=question.id,
                    field="content.valid_answers",
                    issue_type="no_valid_answers",
                    message="No hay respuestas válidas definidas",
                    severity="error",
                    auto_fixable=False,
                ))

        return issues

    def _check_problematic_chars(self, text: str) -> str:
        """Detecta caracteres problemáticos en el texto."""
        problematic = []

        # Caracteres de control
        for char in text:
            if ord(char) < 32 and char not in '\n\r\t':
                problematic.append(f"U+{ord(char):04X}")

        # Comillas tipográficas mal codificadas
        if '\ufffd' in text:  # Replacement character
            problematic.append("U+FFFD")

        return ", ".join(problematic[:5])  # Máximo 5 caracteres reportados

    def _try_auto_fix(
        self,
        question: Question,
        issues: List[ValidationIssue],
    ) -> bool:
        """
        Intenta corregir automáticamente problemas.

        Args:
            question: Pregunta a corregir
            issues: Problemas detectados

        Returns:
            True si se corrigió algo
        """
        fixed = False

        for issue in issues:
            if not issue.auto_fixable:
                continue

            if issue.issue_type == "problematic_chars":
                # Limpiar caracteres problemáticos
                original = question.question_text
                cleaned = ''.join(
                    char for char in original
                    if ord(char) >= 32 or char in '\n\r\t'
                )
                cleaned = cleaned.replace('\ufffd', '')

                if cleaned != original:
                    question.question_text = cleaned
                    fixed = True

        return fixed
