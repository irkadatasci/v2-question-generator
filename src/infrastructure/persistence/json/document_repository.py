"""
Document Repository JSON - Repositorio de documentos en JSON.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ....application.ports.repositories import DocumentRepository
from ....domain.entities.document import Document


class DocumentRepositoryJSON(DocumentRepository):
    """
    Repositorio de documentos usando JSON como almacenamiento.

    Mantiene un índice de documentos procesados para evitar
    reprocesamiento.
    """

    INDEX_FILE = "documents_index.json"

    def __init__(self, base_path: Path):
        """
        Args:
            base_path: Ruta base para almacenar archivos
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

        self._index_path = self._base_path / self.INDEX_FILE

        # Cargar índice existente
        self._index: Dict[str, Dict] = self._load_index()

    def save(self, document: Document) -> None:
        """Guarda un documento."""
        self._index[document.id] = document.to_dict()
        self._save_index()

    def find_by_id(self, document_id: str) -> Optional[Document]:
        """Busca un documento por ID."""
        data = self._index.get(document_id)
        if data:
            return Document.from_dict(data)
        return None

    def find_by_hash(self, file_hash: str) -> Optional[Document]:
        """Busca un documento por hash de archivo."""
        for doc_data in self._index.values():
            if doc_data.get("hash") == file_hash:
                return Document.from_dict(doc_data)
        return None

    def find_all(self) -> List[Document]:
        """Retorna todos los documentos."""
        return [
            Document.from_dict(data)
            for data in self._index.values()
        ]

    def delete(self, document_id: str) -> bool:
        """Elimina un documento."""
        if document_id in self._index:
            del self._index[document_id]
            self._save_index()
            return True
        return False

    def exists(self, document_id: str) -> bool:
        """Verifica si un documento existe."""
        return document_id in self._index

    def find_by_path(self, path: Path) -> Optional[Document]:
        """Busca un documento por ruta de archivo."""
        target_path = str(path)
        for doc_data in self._index.values():
            if str(doc_data.get("path")) == target_path:
                return Document.from_dict(doc_data)
        return None

    def find_pending(self) -> List[Document]:
        """Obtiene documentos pendientes de procesar."""
        return [
            Document.from_dict(data)
            for data in self._index.values()
            if not data.get("processed_at")
        ]

    def find_processed(self) -> List[Document]:
        """Obtiene documentos ya procesados."""
        return [
            Document.from_dict(data)
            for data in self._index.values()
            if data.get("processed_at")
        ]

    def mark_as_processed(self, document_id: str) -> bool:
        """Marca un documento como procesado."""
        document = self.find_by_id(document_id)
        if document:
            document.mark_as_processed()
            self.save(document)
            return True
        return False

    def get_statistics(self, document_id: str) -> dict:
        """Obtiene estadísticas de un documento."""
        document = self.find_by_id(document_id)
        if document:
            return {
                "id": document.id,
                "total_pages": document.total_pages,
                "is_processed": document.is_processed,
                "processed_at": document.processed_at
            }
        return {}

    def _load_index(self) -> Dict[str, Dict]:
        """Carga el índice desde archivo."""
        if self._index_path.exists():
            try:
                with open(self._index_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_index(self) -> None:
        """Guarda el índice a archivo."""
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False, default=str)
