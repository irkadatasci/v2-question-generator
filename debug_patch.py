#!/usr/bin/env python3
"""
Patch temporal para agregar logging a la generación de preguntas.
"""

import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def patch_generate_questions():
    """Parchea el método _parse_response para agregar logging."""
    
    # Importar el módulo original
    from application.use_cases.generate_questions import GenerateQuestionsUseCase
    from domain.entities.question import QuestionType
    import json
    
    # Guardar el método original
    original_parse = GenerateQuestionsUseCase._parse_response
    
    def debug_parse_response(self, content, question_type, sections, document_id):
        """Versión con logging del parse_response."""
        print(f"\n🔍 DEBUG: Parsing response")
        print(f"   Content type: {type(content)}")
        print(f"   Content length: {len(str(content))}")
        print(f"   Question type: {question_type}")
        print(f"   Sections: {len(sections)}")
        print(f"   Document ID: {document_id}")
        
        # Mostrar contenido (primeros 500 caracteres)
        content_str = str(content)[:500]
        print(f"   Content preview: {content_str}...")
        
        # Intentar parsing original
        try:
            questions = original_parse(self, content, question_type, sections, document_id)
            print(f"   Parsed questions: {len(questions)}")
            return questions
        except Exception as e:
            print(f"   ❌ Parse error: {e}")
            return []
    
    # Aplicar el patch
    GenerateQuestionsUseCase._parse_response = debug_parse_response
    print("✅ Patch aplicado: logging agregado a _parse_response")

if __name__ == "__main__":
    patch_generate_questions()