"""
CLI Main - Punto de entrada principal de la CLI.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .commands import (
    ExtractCommand,
    ClassifyCommand,
    GenerateCommand,
    ValidateCommand,
    PipelineCommand,
    ConfigCommand,
)
from ...infrastructure.config import ConfigLoader, Settings


class CLI:
    """
    Interface de línea de comandos para Question Generator v2.

    Comandos disponibles:
    - extract: Extrae secciones de un PDF
    - classify: Clasifica secciones semánticamente
    - generate: Genera preguntas con LLM
    - validate: Valida preguntas generadas
    - pipeline: Ejecuta pipeline completo
    - config: Gestiona configuración
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: Ruta al archivo de configuración
        """
        self._config_path = config_path or Path("config.json")
        self._settings: Optional[Settings] = None

    def run(self, args: Optional[list] = None) -> int:
        """
        Ejecuta la CLI.

        Args:
            args: Argumentos de línea de comandos (None = sys.argv)

        Returns:
            Código de salida (0 = éxito)
        """
        parser = self._create_parser()
        parsed = parser.parse_args(args)

        # Mostrar ayuda si no hay comando
        if not hasattr(parsed, "command") or parsed.command is None:
            parser.print_help()
            return 0

        # Cargar configuración
        try:
            self._load_settings(parsed)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return 1

        # Ejecutar comando
        try:
            return self._execute_command(parsed)
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario")
            return 130
        except Exception as e:
            print(f"Error: {e}")
            if parsed.debug:
                import traceback
                traceback.print_exc()
            return 1

    def _create_parser(self) -> argparse.ArgumentParser:
        """Crea el parser de argumentos."""
        parser = argparse.ArgumentParser(
            prog="qgen",
            description="Question Generator v2 - Genera preguntas desde documentos PDF",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos:
  qgen pipeline documento.pdf --type flashcard
  qgen generate --provider kimi --type multiple_choice
  qgen config show
            """,
        )

        parser.add_argument(
            "--config", "-c",
            type=Path,
            default=Path("config.json"),
            help="Archivo de configuración",
        )

        parser.add_argument(
            "--debug", "-d",
            action="store_true",
            help="Modo debug con más información",
        )

        # Subcomandos
        subparsers = parser.add_subparsers(dest="command", title="comandos")

        # Comando: extract
        extract_parser = subparsers.add_parser(
            "extract",
            help="Extrae secciones de un PDF",
        )
        extract_parser.add_argument("pdf", type=Path, help="Archivo PDF")
        extract_parser.add_argument(
            "--output", "-o",
            type=Path,
            help="Directorio de salida",
        )

        # Comando: classify
        classify_parser = subparsers.add_parser(
            "classify",
            help="Clasifica secciones semánticamente",
        )
        classify_parser.add_argument("document_id", help="ID del documento")
        classify_parser.add_argument(
            "--threshold",
            type=float,
            default=0.7,
            help="Umbral de relevancia (default: 0.7)",
        )

        # Comando: generate
        generate_parser = subparsers.add_parser(
            "generate",
            help="Genera preguntas con LLM",
        )
        generate_parser.add_argument("document_id", help="ID del documento")
        generate_parser.add_argument(
            "--type", "-t",
            choices=["flashcard", "true_false", "multiple_choice", "cloze"],
            default="flashcard",
            help="Tipo de pregunta",
        )
        generate_parser.add_argument(
            "--provider", "-p",
            choices=["kimi", "groq", "openai", "ollama", "ollama_cloud"],
            help="Proveedor de LLM",
        )
        generate_parser.add_argument(
            "--batch-size", "-b",
            type=int,
            default=5,
            help="Tamaño de batch",
        )
        generate_parser.add_argument(
            "--author",
            help="Nombre del autor para atribución en preguntas",
        )

        # Comando: validate
        validate_parser = subparsers.add_parser(
            "validate",
            help="Valida preguntas generadas",
        )
        validate_parser.add_argument("document_id", help="ID del documento")
        validate_parser.add_argument(
            "--level",
            choices=["strict", "moderate", "lenient"],
            default="moderate",
            help="Nivel de validación",
        )
        validate_parser.add_argument(
            "--fix",
            action="store_true",
            help="Intentar corregir automáticamente",
        )

        # Comando: pipeline (completo)
        pipeline_parser = subparsers.add_parser(
            "pipeline",
            help="Ejecuta pipeline completo",
        )
        pipeline_parser.add_argument("pdf", type=Path, help="Archivo PDF")
        pipeline_parser.add_argument(
            "--type", "-t",
            choices=["flashcard", "true_false", "multiple_choice", "cloze", "all"],
            default="flashcard",
            help="Tipo de pregunta (o 'all' para generar todos los tipos)",
        )
        pipeline_parser.add_argument(
            "--provider", "-p",
            choices=["kimi", "groq", "openai", "ollama", "ollama_cloud", "lmstudio"],
            help="Proveedor de LLM (por defecto: kimi)",
        )
        pipeline_parser.add_argument(
            "--skip",
            nargs="+",
            choices=["extract", "classify", "generate", "validate"],
            default=[],
            help="Etapas a omitir",
        )
        pipeline_parser.add_argument(
            "--output", "-o",
            type=Path,
            help="Directorio de salida",
        )
        pipeline_parser.add_argument(
            "--author",
            help="Nombre del autor para atribución en preguntas",
        )

        # Comando: config
        config_parser = subparsers.add_parser(
            "config",
            help="Gestiona configuración",
        )
        config_subparsers = config_parser.add_subparsers(dest="config_action")

        config_subparsers.add_parser("show", help="Muestra configuración actual")
        config_subparsers.add_parser("init", help="Crea archivo de configuración")

        providers_parser = config_subparsers.add_parser(
            "providers",
            help="Lista proveedores configurados"
        )

        return parser

    def _load_settings(self, parsed) -> None:
        """Carga la configuración."""
        config_path = getattr(parsed, "config", self._config_path)

        loader = ConfigLoader(config_path)
        self._settings = loader.load()

        if parsed.debug:
            self._settings.debug = True

    def _execute_command(self, parsed) -> int:
        """Ejecuta el comando especificado."""
        command = parsed.command

        if command == "extract":
            cmd = ExtractCommand(self._settings)
            return cmd.execute(parsed.pdf, parsed.output)

        elif command == "classify":
            cmd = ClassifyCommand(self._settings)
            return cmd.execute(parsed.document_id, parsed.threshold)

        elif command == "generate":
            cmd = GenerateCommand(self._settings)
            return cmd.execute(
                parsed.document_id,
                parsed.type,
                parsed.provider,
                parsed.batch_size,
                parsed.author,  # Pass author argument
            )

        elif command == "validate":
            cmd = ValidateCommand(self._settings)
            return cmd.execute(
                parsed.document_id,
                parsed.level,
                parsed.fix,
            )

        elif command == "pipeline":
            cmd = PipelineCommand(self._settings)
            return cmd.execute(
                parsed.pdf,
                parsed.type,
                parsed.provider,
                parsed.skip,
                parsed.output,
                parsed.author,  # Pass author argument
            )

        elif command == "config":
            cmd = ConfigCommand(self._settings)
            action = getattr(parsed, "config_action", "show")
            return cmd.execute(action)

        return 1


def main():
    """Punto de entrada principal."""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
