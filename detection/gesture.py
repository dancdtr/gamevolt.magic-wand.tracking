from __future__ import annotations

from collections.abc import Iterator
from functools import cached_property

from detection.gesture_point import GesturePoint
from detection.turn import TurnType
from detection.turn_point import TurnPoint
from gamevolt.maths.extremum import Extremum
from gamevolt.maths.vector_2 import Vector2


class Gesture:
    def __init__(
        self,
        points: list[GesturePoint],
        average_direction: Vector2,
        duration: float,
        extrema: list[Extremum],
        turn_points: list[TurnPoint],
    ) -> None:
        self.points = points
        self.azimuth = average_direction
        self.turn_points = turn_points
        self.duration = duration
        self.extrema = extrema

    def iter_x_extrema(self) -> Iterator[Extremum]:
        return (e for e in self.extrema if e.is_x())

    def iter_y_extrema(self) -> Iterator[Extremum]:
        return (e for e in self.extrema if e.is_y())

    def iter_x_turn_points(self) -> Iterator[TurnPoint]:
        return (tp for tp in self.turn_points if tp.type.in_x())

    def iter_y_turn_points(self) -> Iterator[TurnPoint]:
        return (tp for tp in self.turn_points if tp.type.in_y())

    def iter_turn_types(self) -> Iterator[TurnType]:
        return (tp.type for tp in self.turn_points)

    def iter_x_turn_types(self) -> Iterator[TurnType]:
        return (tp.type for tp in self.turn_points if tp.type.in_x())

    def iter_y_turn_types(self) -> Iterator[TurnType]:
        return (tp.type for tp in self.turn_points if tp.type.in_y())

    # ---------- Lazy “last *” lookups ----------

    @property
    def first_turn_point(self) -> TurnPoint | None:
        return self.turn_points[0] if self.turn_points else None

    @property
    def first_x_turn_point(self) -> TurnPoint | None:
        for tp in self.turn_points:
            if tp.type.in_x():
                return tp
        return None

    @property
    def first_y_turn_point(self) -> TurnPoint | None:
        for tp in self.turn_points:
            if tp.type.in_y():
                return tp
        return None

    @property
    def last_turn_point(self) -> TurnPoint | None:
        return self.turn_points[-1] if self.turn_points else None

    @property
    def last_x_turn_point(self) -> TurnPoint | None:
        for tp in reversed(self.turn_points):
            if tp.type.in_x():
                return tp
        return None

    @property
    def last_y_turn_point(self) -> TurnPoint | None:
        for tp in reversed(self.turn_points):
            if tp.type.in_y():
                return tp
        return None

    # ---------- Direction helpers ----------

    @cached_property
    def direction_abs(self) -> Vector2:
        return Vector2(abs(self.azimuth.x), abs(self.azimuth.y))

    @property
    def min_direction_abs(self) -> float:
        d = self.direction_abs
        return d.x if d.x < d.y else d.y

    @property
    def max_direction_abs(self) -> float:
        d = self.direction_abs
        return d.x if d.x > d.y else d.y
