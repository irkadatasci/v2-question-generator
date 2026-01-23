"""
Coordinates Value Object - Posición y dimensiones en el PDF.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Coordinates:
    """
    Value object que representa coordenadas y dimensiones en un PDF.

    Es inmutable (frozen=True) y se compara por valor.

    Attributes:
        x: Posición horizontal (desde el borde izquierdo)
        y: Posición vertical (desde el borde superior)
        width: Ancho del elemento
        height: Alto del elemento
        page: Número de página (opcional, para contexto)
    """

    x: float
    y: float
    width: float = 0.0
    height: float = 0.0

    def __post_init__(self) -> None:
        """Valida que las coordenadas sean válidas."""
        if self.x < 0 or self.y < 0:
            raise ValueError("Coordenadas no pueden ser negativas")
        if self.width < 0 or self.height < 0:
            raise ValueError("Dimensiones no pueden ser negativas")

    @classmethod
    def from_dict(cls, data: Dict) -> "Coordinates":
        """
        Crea Coordinates desde un diccionario.

        Args:
            data: Diccionario con keys 'x', 'y', 'width', 'height'

        Returns:
            Nueva instancia de Coordinates
        """
        return cls(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            width=float(data.get("width", data.get("ancho", 0))),
            height=float(data.get("height", data.get("alto", 0))),
        )

    def to_dict(self) -> Dict:
        """Convierte a diccionario."""
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
        }

    @property
    def area(self) -> float:
        """Calcula el área del elemento."""
        return self.width * self.height

    @property
    def center(self) -> tuple:
        """Calcula el centro del elemento."""
        return (self.x + self.width / 2, self.y + self.height / 2)

    def contains_point(self, point_x: float, point_y: float) -> bool:
        """
        Verifica si un punto está dentro del área.

        Args:
            point_x: Coordenada X del punto
            point_y: Coordenada Y del punto

        Returns:
            True si el punto está dentro del área
        """
        return (
            self.x <= point_x <= self.x + self.width
            and self.y <= point_y <= self.y + self.height
        )

    def overlaps(self, other: "Coordinates") -> bool:
        """
        Verifica si hay superposición con otras coordenadas.

        Args:
            other: Otras coordenadas a comparar

        Returns:
            True si hay superposición
        """
        return not (
            self.x + self.width < other.x
            or other.x + other.width < self.x
            or self.y + self.height < other.y
            or other.y + other.height < self.y
        )

    def __str__(self) -> str:
        return f"({self.x:.2f}, {self.y:.2f}) [{self.width:.2f}x{self.height:.2f}]"
