from dataclasses import dataclass

from vector_2 import Vector2


@dataclass
class GesturePoint:
    velocity: Vector2
    timestamp: int
