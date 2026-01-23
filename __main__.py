"""
Punto de entrada para ejecución como módulo.

Uso:
    python -m v2_question_generator
    python -m v2_question_generator pipeline documento.pdf --type flashcard
"""

from src.interface.cli.main import main

if __name__ == "__main__":
    main()
