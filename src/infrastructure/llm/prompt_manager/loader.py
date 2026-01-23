"""
Prompt Loader - Carga prompts desde archivos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class PromptMetadata:
    """Metadata de un prompt."""
    version: str
    created_at: datetime
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    is_active: bool = False


@dataclass
class LoadedPrompt:
    """Prompt cargado desde archivo."""
    content: str
    metadata: PromptMetadata
    file_path: Path


class PromptLoader:
    """
    Carga prompts desde el sistema de archivos.

    Estructura esperada:
    prompts/
    ├── flashcard/
    │   ├── v1.0.md
    │   ├── v1.1.md
    │   └── metadata.json
    ├── true_false/
    │   ├── v1.0.md
    │   └── metadata.json
    └── ...
    """

    def __init__(self, base_path: Path):
        """
        Args:
            base_path: Ruta base donde están los prompts
        """
        self._base_path = Path(base_path)

    def load(
        self,
        question_type: str,
        version: Optional[str] = None,
    ) -> LoadedPrompt:
        """
        Carga un prompt específico.

        Args:
            question_type: Tipo de pregunta (flashcard, true_false, etc.)
            version: Versión específica (None = activa)

        Returns:
            LoadedPrompt con contenido y metadata
        """
        type_path = self._base_path / question_type

        if not type_path.exists():
            raise FileNotFoundError(f"No existe directorio de prompts: {type_path}")

        # Obtener versión a cargar
        if version is None:
            version = self._get_active_version(type_path)

        # Buscar archivo de prompt
        prompt_file = self._find_prompt_file(type_path, version)

        if not prompt_file.exists():
            raise FileNotFoundError(f"No existe prompt versión {version}: {prompt_file}")

        # Cargar contenido
        content = prompt_file.read_text(encoding="utf-8")

        # Cargar metadata
        metadata = self._load_metadata(type_path, version)

        return LoadedPrompt(
            content=content,
            metadata=metadata,
            file_path=prompt_file,
        )

    def list_versions(self, question_type: str) -> List[str]:
        """
        Lista versiones disponibles de un prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Lista de versiones disponibles
        """
        type_path = self._base_path / question_type

        if not type_path.exists():
            return []

        versions = []
        for file in type_path.glob("v*.md"):
            # Extraer versión del nombre: v1.0.md -> 1.0
            version = file.stem.replace("v", "")
            versions.append(version)

        return sorted(versions, key=lambda v: [int(x) for x in v.split(".")])

    def get_active_version(self, question_type: str) -> str:
        """
        Obtiene la versión activa de un prompt.

        Args:
            question_type: Tipo de pregunta

        Returns:
            Versión activa
        """
        type_path = self._base_path / question_type
        return self._get_active_version(type_path)

    def set_active_version(self, question_type: str, version: str) -> None:
        """
        Establece la versión activa de un prompt.

        Args:
            question_type: Tipo de pregunta
            version: Versión a activar
        """
        type_path = self._base_path / question_type
        metadata_file = type_path / "metadata.json"

        metadata = {}
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

        metadata["active_version"] = version
        metadata["updated_at"] = datetime.now().isoformat()

        metadata_file.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def save_version(
        self,
        question_type: str,
        version: str,
        content: str,
        description: str = "",
        set_active: bool = False,
    ) -> Path:
        """
        Guarda una nueva versión de prompt.

        Args:
            question_type: Tipo de pregunta
            version: Número de versión
            content: Contenido del prompt
            description: Descripción de cambios
            set_active: Si establecer como versión activa

        Returns:
            Ruta del archivo creado
        """
        type_path = self._base_path / question_type
        type_path.mkdir(parents=True, exist_ok=True)

        # Guardar archivo de prompt
        prompt_file = type_path / f"v{version}.md"
        prompt_file.write_text(content, encoding="utf-8")

        # Actualizar metadata
        metadata_file = type_path / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

        if "versions" not in metadata:
            metadata["versions"] = {}

        metadata["versions"][version] = {
            "created_at": datetime.now().isoformat(),
            "description": description,
        }

        if set_active:
            metadata["active_version"] = version

        metadata_file.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        return prompt_file

    def _get_active_version(self, type_path: Path) -> str:
        """Obtiene versión activa desde metadata."""
        metadata_file = type_path / "metadata.json"

        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            if "active_version" in metadata:
                return metadata["active_version"]

        # Fallback: última versión disponible
        versions = []
        for file in type_path.glob("v*.md"):
            version = file.stem.replace("v", "")
            versions.append(version)

        if versions:
            return sorted(versions, key=lambda v: [int(x) for x in v.split(".")])[-1]

        raise ValueError(f"No hay prompts disponibles en {type_path}")

    def _find_prompt_file(self, type_path: Path, version: str) -> Path:
        """Busca el archivo de prompt para una versión."""
        # Intentar formato v1.0.md
        prompt_file = type_path / f"v{version}.md"
        if prompt_file.exists():
            return prompt_file

        # Intentar sin prefijo v
        prompt_file = type_path / f"{version}.md"
        if prompt_file.exists():
            return prompt_file

        return type_path / f"v{version}.md"

    def _load_metadata(self, type_path: Path, version: str) -> PromptMetadata:
        """Carga metadata de una versión específica."""
        metadata_file = type_path / "metadata.json"

        if not metadata_file.exists():
            return PromptMetadata(
                version=version,
                created_at=datetime.now(),
            )

        data = json.loads(metadata_file.read_text(encoding="utf-8"))
        version_data = data.get("versions", {}).get(version, {})

        return PromptMetadata(
            version=version,
            created_at=datetime.fromisoformat(version_data.get("created_at", datetime.now().isoformat())),
            description=version_data.get("description", ""),
            author=version_data.get("author", ""),
            tags=version_data.get("tags", []),
            is_active=data.get("active_version") == version,
        )
