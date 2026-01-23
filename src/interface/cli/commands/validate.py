"""
Validate Command - Comando para validar preguntas.
"""

from ....infrastructure.config import Settings
from ....infrastructure.persistence import QuestionRepositoryJSON
from ....application.use_cases import ValidateQuestionsUseCase, ValidateQuestionsRequest


class ValidateCommand:
    """Comando para validar preguntas generadas."""

    def __init__(self, settings: Settings):
        """
        Args:
            settings: Configuración de la aplicación
        """
        self._settings = settings

    def execute(
        self,
        document_id: str,
        level: str = "moderate",
        auto_fix: bool = False,
    ) -> int:
        """
        Ejecuta la validación de preguntas.

        Args:
            document_id: ID del documento
            level: Nivel de validación
            auto_fix: Si intentar correcciones automáticas

        Returns:
            Código de salida
        """
        print(f"🔍 Validando preguntas del documento: {document_id}")
        print(f"   Nivel: {level}")
        print(f"   Auto-fix: {'Sí' if auto_fix else 'No'}")

        # Crear repositorio
        question_repo = QuestionRepositoryJSON(
            self._settings.paths.output_dir
        )

        # Crear caso de uso
        use_case = ValidateQuestionsUseCase(
            question_repository=question_repo,
        )

        # Ejecutar
        request = ValidateQuestionsRequest(
            document_id=document_id,
            validation_level=level,
            auto_fix=auto_fix,
            export_invalid=True,
        )

        result = use_case.execute(request)

        if result.success:
            print(f"\n✅ Validación completada")
            print(f"   📊 Total preguntas: {result.total_questions}")
            print(f"   ✓ Válidas: {result.valid_questions}")
            print(f"   ✗ Inválidas: {result.invalid_questions}")

            if auto_fix and result.fixed_questions > 0:
                print(f"   🔧 Corregidas: {result.fixed_questions}")

            if result.issues_by_type:
                print(f"   ⚠️  Problemas detectados:")
                for issue_type, count in result.issues_by_type.items():
                    print(f"      - {issue_type}: {count}")

            if result.output_invalid_path:
                print(f"   📁 Inválidas exportadas: {result.output_invalid_path}")

            print(f"   ⏱️  Tiempo: {result.execution_time_seconds:.2f}s")

            # Retornar código según ratio de éxito
            if result.invalid_questions == 0:
                return 0
            elif result.valid_questions > result.invalid_questions:
                return 0
            else:
                print(f"\n⚠️  Más de la mitad de las preguntas son inválidas")
                return 1
        else:
            print(f"❌ Error: {result.error_message}")
            return 1
