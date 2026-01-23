"""
Origin Value Object - Información de trazabilidad al origen.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from .coordinates import Coordinates


@dataclass(frozen=True)
class Origin:
    """
    Value object que representa la trazabilidad de una pregunta a su origen.

    Mantiene la información necesaria para vincular una pregunta generada
    con la sección específica del documento fuente.

    Attributes:
        document_id: ID del documento fuente
        section_id: ID de la sección fuente
        title: Título de la sección
        page: Número de página
        coordinates: Coordenadas en el PDF
        text_length: Longitud del texto original
        author: Autor mencionado (si aplica)
        source: Fuente específica (código, manual, etc.)
    """

    document_id: str
    section_id: int
    title: str
    page: int
    coordinates: Coordinates
    text_length: int
    author: Optional[str] = None
    source: Optional[str] = None

    @classmethod
    def from_section(cls, section: "Section", document_id: str) -> "Origin":
        """
        Crea Origin desde una Section.

        Args:
            section: Sección fuente
            document_id: ID del documento

        Returns:
            Nueva instancia de Origin
        """
        return cls(
            document_id=document_id,
            section_id=section.id,
            title=section.title,
            page=section.page,
            coordinates=section.coordinates,
            text_length=section.text_length,
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "Origin":
        """
        Crea Origin desde un diccionario.

        Args:
            data: Diccionario con datos de origen

        Returns:
            Nueva instancia de Origin
        """
        coords_data = data.get("coordenadas", data.get("coordinates", {}))
        if isinstance(coords_data, Coordinates):
            coordinates = coords_data
        else:
            coordinates = Coordinates.from_dict(coords_data)

        return cls(
            document_id=data.get("document_id", ""),
            section_id=int(data.get("section_id", data.get("id_seccion", 0))),
            title=data.get("titulo", data.get("title", "")),
            page=int(data.get("pagina", data.get("page", 0))),
            coordinates=coordinates,
            text_length=int(data.get("longitud_texto", data.get("text_length", 0))),
            author=data.get("autor", data.get("author")),
            source=data.get("fuente", data.get("source")),
        )

    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización."""
        result = {
            "document_id": self.document_id,
            "section_id": self.section_id,
            "titulo": self.title,
            "pagina": self.page,
            "coordenadas": self.coordinates.to_dict(),
            "longitud_texto": self.text_length,
        }

        if self.author:
            result["autor"] = self.author
        if self.source:
            result["fuente"] = self.source

        return result

    def to_lexquest_format(self) -> Dict:
        """Convierte a formato LexQuest simplificado."""
        return {
            "titulo": self.title,
            "pagina": self.page,
            "coordenadas": {"x": self.coordinates.x, "y": self.coordinates.y},
            "longitud_texto": self.text_length,
            "elemento_visual": {
                "ancho": self.coordinates.width,
                "alto": self.coordinates.height,
            },
        }

    def matches_section(self, section_title: str, section_page: int) -> bool:
        """
        Verifica si el origen coincide con una sección dada.

        Args:
            section_title: Título de la sección a comparar
            section_page: Página de la sección a comparar

        Returns:
            True si coinciden
        """
        return self.title == section_title and self.page == section_page

    def __str__(self) -> str:
        return f"[{self.section_id}] {self.title} (Pág. {self.page})"
