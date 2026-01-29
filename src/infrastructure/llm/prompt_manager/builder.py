"""
Prompt Builder - Construye prompts dinámicos con secciones.
"""

from typing import List, Optional
from pathlib import Path
from ....domain.entities.section import Section
from ....domain.entities.question import QuestionType


class PromptBuilder:
    """
    Construye user prompts dinámicos con secciones.

    Responsable de formatear las secciones en el prompt
    de manera óptima para el LLM.
    """

    # Templates por tipo de pregunta para el contenido de las secciones
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
        # Fallback por defecto
        "default": """
### Sección {index}: {title}
**Página:** {page}
**Contenido:**
{text}
---
"""
    }

    def __init__(self, templates_dir: Path, author: Optional[str] = None):
        """
        Inicializa el PromptBuilder.
        Args:
            templates_dir: Directorio donde están los templates .md
            author: Nombre del autor (opcional) para atribución
        """
        self.templates_dir = templates_dir
        self.author = author
        
        # Cargar templates base
        self.header_template = self._load_template("header.md") or "# Contexto\n\n"
        self.footer_template = self._load_template("footer.md") or "\n\n---"

    def _load_template(self, filename: str) -> Optional[str]:
        """Carga un template desde el sistema de archivos."""
        path = self.templates_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def _get_context_instructions(self) -> str:
        """Genera instrucciones dinámicas sobre cómo referenciar la fuente."""
        if self.author:
            return f"""
## REFERENCIAS DE AUTORÍA (MODO AUTOR)

El contenido proviene de la obra de: **{self.author}**.

Reglas de Atribución:
1.  **Atributo Directo**: Cuando expliques teorías, distinciones o definiciones específicas de la doctrina, USA el nombre del autor.
    *   ✅ "{self.author} distingue entre..."
    *   ✅ "Para {self.author}, el concepto es..."
2.  **PROHIBICIÓN ABSOLUTA**: NO uses referencias genéricas al soporte físico.
    *   ❌ "según el texto", "el documento señala", "el fragmento indica", "citado en el texto", "el pasaje", "el material".
"""
        else:
            return """
## ESTILO ACADÉMICO (MODO DIRECTO)

Reglas de Estilo:
1.  **Afirmaciones Categóricas**: Trata el contenido como "Hechos Veridados". No cites la fuente.
    *   ✅ "El plazo de prescripción es de 5 años."
    *   ❌ "El texto dice que el plazo es de 5 años."
2.  **PROHIBICIÓN ABSOLUTA**: NO uses metareferencias al documento.
    *   ❌ "según el texto", "en este documento", "el autor menciona", "el pasaje describe", "la sección indica".
"""

    def build(self, sections: List[Section], question_type: str) -> str:
        """Construye el prompt completo."""
        
        # Convertir string a Enum si es necesario para buscar en SECTION_TEMPLATES
        try:
            q_type_enum = QuestionType(question_type)
        except ValueError:
            # Si falla (ej 'all'), usar un default seguro para templates de sección
            q_type_enum = QuestionType.FLASHCARD

        # 1. Cargar el System Prompt del tipo específico (v2.0)
        type_template = self._load_template(f"{question_type}/v2.0.md")
        
        # Fallback para cloze v1.0
        if not type_template and question_type == "cloze":
             type_template = self._load_template(f"{question_type}/v1.0.md")

        if not type_template:
            # Si no hay archivo, usar un template mínimo por defecto para evitar crash
            type_template = "Genera preguntas basadas en el contexto proporcionado."

        # 2. Inyectar instrucciones de contexto dinámicas
        context_instructions = self._get_context_instructions()
        
        if "{{context_instructions}}" in type_template:
            type_template = type_template.replace("{{context_instructions}}", context_instructions)
        else:
            # Inserción inteligente si no hay placeholder
            type_template = context_instructions + "\n\n" + type_template

        # 3. Construir el texto de las secciones
        sections_text = []
        for i, section in enumerate(sections, 1):
            # Obtener template de sección
            sec_tmpl = self.SECTION_TEMPLATES.get(q_type_enum, self.SECTION_TEMPLATES["default"])
            
            cleaned_text = self._clean_text(section.text)
            sections_text.append(sec_tmpl.format(
                index=i,
                title=section.title or f"Sección {section.id}",
                page=section.page,
                text=cleaned_text
            ))

        # 4. Ensamblar todo
        full_content = "\n".join(sections_text)
        
        return f"{self.header_template}\n\n{type_template}\n\n{full_content}\n\n{self.footer_template}"

    def build_with_examples(
        self,
        sections: List[Section],
        question_type: QuestionType,
        examples: List[dict],
    ) -> str:
        """Construye prompt con ejemplos."""
        base_prompt = self.build(sections, question_type.value) # build espera str
        
        parts = [base_prompt]
        if examples:
            parts.append("\n## Ejemplos de formato esperado\n\n")
            parts.append("```json\n")
            import json
            parts.append(json.dumps(examples[:2], indent=2, ensure_ascii=False))
            parts.append("\n```\n\n")
            
        return "".join(parts)

    def estimate_tokens(
        self,
        sections: List[Section],
        question_type: QuestionType,
    ) -> int:
        """Estima tokens del prompt completo."""
        prompt = self.build(sections, question_type.value)
        return len(prompt) // 4

    def _clean_text(self, text: str) -> str:
        """Limpia el texto para el prompt."""
        if not text:
            return ""
        lines = text.split("\n")
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        return "\n".join(cleaned_lines)
