"""
Document Repository Interface - Contrato para persistencia de documentos.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ....domain.entities.document import Document


class DocumentRepository(ABC):
    """
    Interface abstracta para repositorio de documentos.

    Define el contrato que deben implementar los adaptadores de
    persistencia de documentos.
    """

    @abstractmethod
    def save(self, document: Document) -> None:
        """
        Guarda un documento.

        Args:
            document: Documento a guardar
        """
        pass

    @abstractmethod
    def find_by_id(self, document_id: str) -> Optional[Document]:
        """
        Busca un documento por ID.

        Args:
            document_id: ID del documento

        Returns:
            Documento encontrado o None
        """
        pass

    @abstractmethod
    def find_by_hash(self, file_hash: str) -> Optional[Document]:
        """
        Busca un documento por hash de archivo.

        Args:
            file_hash: Hash MD5 del archivo

        Returns:
            Documento encontrado o None
        """
        pass

    @abstractmethod
    def find_by_path(self, path: Path) -> Optional[Document]:
        """
        Busca un documento por ruta de archivo.

        Args:
            path: Ruta del archivo PDF

        Returns:
            Documento encontrado o None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Document]:
        """
        Obtiene todos los documentos.

        Returns:
            Lista de documentos
        """
        pass

    @abstractmethod
    def find_processed(self) -> List[Document]:
        """
        Obtiene documentos ya procesados.

        Returns:
            Lista de documentos procesados
        """
        pass

    @abstractmethod
    def find_pending(self) -> List[Document]:
        """
        Obtiene documentos pendientes de procesar.

        Returns:
            Lista de documentos pendientes
        """
        pass

    @abstractmethod
    def exists(self, document_id: str) -> bool:
        """
        Verifica si existe un documento.

        Args:
            document_id: ID del documento

        Returns:
            True si existe
        """
        pass

    @abstractmethod
    def delete(self, document_id: str) -> bool:
        """
        Elimina un documento y sus datos asociados.

        Args:
            document_id: ID del documento

        Returns:
            True si se eliminó
        """
        pass

    @abstractmethod
    def mark_as_processed(self, document_id: str) -> bool:
        """
        Marca un documento como procesado.

        Args:
            document_id: ID del documento

        Returns:
            True si se actualizó
        """
        pass

    @abstractmethod
    def get_statistics(self, document_id: str) -> dict:
        """
        Obtiene estadísticas de un documento.

        Args:
            document_id: ID del documento

        Returns:
            Diccionario con estadísticas
        """
        pass
