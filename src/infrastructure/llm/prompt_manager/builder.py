"""
Prompt Builder - Construye prompts dinámicos con secciones.
"""

from typing import List, Optional
from ....domain.entities.section import Section
from ....domain.entities.question import QuestionType


class PromptBuilder:
    """
    Construye user prompts dinámicos con secciones.

    Responsable de formatear las secciones en el prompt
    de manera óptima para el LLM.
    """

    # Templates por tipo de pregunta
    SECTION_TEMPLATES = {
        QuestionType.FLASHCARD: """
### Sección {index}: {title}
**Página:** {page}
**Texto:**
{text}
---
""",
        QuestionType.TRUE_FALSE: """
### Sección {index}: {title}
**Página:** {page}
**Contenido:**
{text}
---
""",
        QuestionType.MULTIPLE_CHOICE: """
### Sección {index}: {title}
**Página:** {page}
**Material de referencia:**
{text}
---
""",
        QuestionType.CLOZE: """
### Sección {index}: {title}
**Página:** {page}
**Texto base:**
{text}
---
""",
    }

    HEADER_TEMPLATE = """
# Contexto del documento

A continuación se presentan {count} secciones de un documento legal.
Genera preguntas de tipo **{question_type}** basándote en el contenido.

---

"""

    FOOTER_TEMPLATE = """

---

## Instrucciones finales

- Genera preguntas únicamente basadas en el texto proporcionado.
- No inventes información que no esté en las secciones.
- Asegúrate de que cada pregunta tenga una única respuesta correcta.
- Incluye la referencia a la sección de origen en cada pregunta.

**Responde en formato JSON.**
"""

    def __init__(self, include_context: bool = True):
        """
        Args:
            include_context: Si incluir header/footer de contexto
        """
        self._include_context = include_context

    def build(
        self,
        sections: List[Section],
        question_type: QuestionType,
    ) -> str:
        """
        Construye el user prompt con las secciones.

        Args:
            sections: Lista de secciones a incluir
            question_type: Tipo de pregunta

        Returns:
            User prompt construido
        """
        parts = []

        # Header
        if self._include_context:
            parts.append(self.HEADER_TEMPLATE.format(
                count=len(sections),
                question_type=self._format_question_type(question_type),
            ))

        # Secciones
        template = self.SECTION_TEMPLATES.get(
            question_type,
            self.SECTION_TEMPLATES[QuestionType.FLASHCARD]
        )

        for i, section in enumerate(sections, 1):
            parts.append(template.format(
                index=i,
                title=section.title or f"Sección {section.id}",
                page=section.page,
                text=self._clean_text(section.text),
            ))

        # Footer
        if self._include_context:
            parts.append(self.FOOTER_TEMPLATE)

        return "".join(parts)

    def build_with_examples(
        self,
        sections: List[Section],
        question_type: QuestionType,
        examples: List[dict],
    ) -> str:
        """
        Construye prompt con ejemplos (few-shot).

        Args:
            sections: Secciones a procesar
            question_type: Tipo de pregunta
            examples: Ejemplos de preguntas bien formadas

        Returns:
            User prompt con ejemplos
        """
        parts = []

        # Ejemplos
        if examples:
            parts.append("\n## Ejemplos de formato esperado\n\n")
            parts.append("```json\n")
            import json
            parts.append(json.dumps(examples[:2], indent=2, ensure_ascii=False))
            parts.append("\n```\n\n")

        # Contenido principal
        parts.append(self.build(sections, question_type))

        return "".join(parts)

    def estimate_tokens(
        self,
        sections: List[Section],
        question_type: QuestionType,
    ) -> int:
        """
        Estima tokens del prompt construido.

        Usa aproximación de 4 caracteres por token.

        Args:
            sections: Secciones a incluir
            question_type: Tipo de pregunta

        Returns:
            Tokens estimados
        """
        prompt = self.build(sections, question_type)
        # Aproximación: 4 caracteres por token (promedio)
        return len(prompt) // 4

    def _clean_text(self, text: str) -> str:
        """Limpia el texto para el prompt."""
        # Remover espacios excesivos
        lines = text.split("\n")
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        return "\n".join(cleaned_lines)

    def _format_question_type(self, question_type: QuestionType) -> str:
        """Formatea el tipo de pregunta para mostrar."""
        formats = {
            QuestionType.FLASHCARD: "Flashcard (pregunta-respuesta)",
            QuestionType.TRUE_FALSE: "Verdadero/Falso",
            QuestionType.MULTIPLE_CHOICE: "Opción Múltiple",
            QuestionType.CLOZE: "Completar espacios (Cloze)",
        }
        return formats.get(question_type, question_type.value)
