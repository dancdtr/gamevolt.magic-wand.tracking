from dataclasses import dataclass
from typing import Self


@dataclass
class Vector2:
    x: float
    y: float

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"

    def __format__(self, spec: str) -> str:
        signed_spec = "+" + spec
        return f"({format(self.x, signed_spec)}, " f"{format(self.y, signed_spec)})"

    @classmethod
    def from_average(cls, points: list[Self]) -> Self:
        x = sum([p.x for p in points]) / len(points)
        y = sum([p.y for p in points]) / len(points)
        return cls(x, y)
