"""
Question Generator v2 - Generador de preguntas desde documentos PDF.

Arquitectura Clean/Hexagonal con capas:
- domain/: Entidades y value objects
- application/: Casos de uso y puertos
- infrastructure/: Adaptadores e implementaciones
- interface/: CLI y puntos de entrada

Uso:
    from v2_question_generator import CLI
    cli = CLI()
    cli.run()
"""

__version__ = "2.0.0"

from .interface import CLI

__all__ = ["CLI", "__version__"]
