import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Self


@dataclass
class Vector2:
    x: float
    y: float

    @classmethod
    def from_average(cls, points: list[Self]) -> Self:
        x = sum([p.x for p in points]) / len(points)
        y = sum([p.y for p in points]) / len(points)
        return cls(x, y)

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"

    def __format__(self, spec: str) -> str:
        signed_spec = "+" + spec
        return f"({format(self.x, signed_spec)}, " f"{format(self.y, signed_spec)})"

    def get_bearing(self) -> float:
        x, y = self.x, self.y
        if x == 0 and y == 0:
            raise ValueError("Zero vector has no bearing.")
        a = (math.degrees(math.atan2(-y, x)) + 270) % 360.0
        return 0.0 if abs(a) < 1e-12 else a
