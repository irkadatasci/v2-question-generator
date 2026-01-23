"""
Document Entity - Representa un documento PDF fuente.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import hashlib


@dataclass
class Document:
    """
    Entidad que representa un documento PDF fuente.

    Un documento es la unidad de entrada del sistema. Contiene metadata
    sobre el archivo PDF y su estado de procesamiento.

    Attributes:
        id: Identificador único del documento (hash del archivo)
        path: Ruta al archivo PDF
        name: Nombre del documento
        hash: Hash MD5 del contenido del archivo
        total_pages: Número total de páginas
        created_at: Fecha de creación del registro
        processed_at: Fecha de procesamiento (si fue procesado)
    """

    id: str
    path: Path
    name: str
    hash: str
    total_pages: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

    @classmethod
    def from_path(cls, pdf_path: Path) -> "Document":
        """
        Crea un Document desde una ruta de archivo PDF.

        Args:
            pdf_path: Ruta al archivo PDF

        Returns:
            Nueva instancia de Document

        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

        # Calcular hash del archivo
        with open(pdf_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()

        return cls(
            id=file_hash[:12],  # Primeros 12 caracteres del hash
            path=pdf_path,
            name=pdf_path.stem,
            hash=file_hash,
        )

    def mark_as_processed(self) -> None:
        """Marca el documento como procesado."""
        self.processed_at = datetime.now()

    @property
    def is_processed(self) -> bool:
        """Indica si el documento ya fue procesado."""
        return self.processed_at is not None

    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario."""
        return {
            "id": self.id,
            "path": str(self.path),
            "name": self.name,
            "hash": self.hash,
            "total_pages": self.total_pages,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """Crea una entidad desde un diccionario."""
        return cls(
            id=data["id"],
            path=Path(data["path"]),
            name=data["name"],
            hash=data["hash"],
            total_pages=data.get("total_pages", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            processed_at=datetime.fromisoformat(data["processed_at"]) if data.get("processed_at") else None,
        )

    def __hash__(self) -> int:
        return hash(self.hash)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return False
        return self.hash == other.hash
