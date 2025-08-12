from dataclasses import dataclass

from classification.extremum import Extremum
from detection.gesture_point import GesturePoint
from vector_2 import Vector2


@dataclass
class Gesture:
    points: list[GesturePoint]
    direction: Vector2
    direction_abs: Vector2
    duration: float
    extrema: list[Extremum]
    onset_heading: Vector2

    first_extremum: Extremum
    first_extremum_index: int | None

    x_extrema: list[Extremum]
    y_extrema: list[Extremum]

    @property
    def min_direction_abs(self) -> float:
        return min(self.direction_abs.x, self.direction_abs.y)

    @property
    def max_direction_abs(self) -> float:
        return max(self.direction_abs.x, self.direction_abs.y)
