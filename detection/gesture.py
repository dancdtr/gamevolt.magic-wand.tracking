from classification.extremum import Extremum
from detection.gesture_point import GesturePoint
from detection.turn import TurnType
from detection.turn_point import TurnPoint
from vector_2 import Vector2


class Gesture:
    def __init__(
        self,
        points: list[GesturePoint],
        direction: Vector2,
        direction_abs: Vector2,
        duration: float,
        extrema: list[Extremum],
        onset_heading: Vector2,
        first_extremum: Extremum,
        first_extremum_index: int | None,
        turn_points: list[TurnPoint],
    ) -> None:
        self.points = points
        self.direction = direction
        self.direction_abs = direction_abs
        self.duration = duration
        self.onset_heading = onset_heading
        self.first_extremum = first_extremum
        self.first_extremum_index = first_extremum_index
        self.extrema = extrema

        self.min_direction_abs = min(direction_abs.x, direction_abs.y)
        self.max_direction_abs = max(direction_abs.x, direction_abs.y)

        self.x_extrema = [e for e in self.extrema if e in (Extremum.X_MIN, Extremum.X_MAX)]
        self.y_extrema = [e for e in self.extrema if e in (Extremum.Y_MIN, Extremum.Y_MAX)]

        x_turn_points = [turn for turn in turn_points if turn.type in (TurnType.LEFT_TO_RIGHT, TurnType.RIGHT_TO_LEFT)]
        y_turn_points = [turn for turn in turn_points if turn.type in (TurnType.UP_TO_DOWN, TurnType.DOWN_TO_UP)]

        last_turn_point: TurnPoint | None = None if len(turn_points) == 0 else turn_points[-1]
        last_x_turn_point: TurnPoint | None = None if len(x_turn_points) == 0 else x_turn_points[-1]
        last_y_turn_point: TurnPoint | None = None if len(y_turn_points) == 0 else y_turn_points[-1]

        turn_types = [turn_point.type for turn_point in turn_points]

        self.turn_points = turn_points
        self.x_turn_points = x_turn_points
        self.y_turn_points = y_turn_points
        self.last_turn_point = last_turn_point
        self.last_x_turn_point = last_x_turn_point
        self.last_y_turn_point = last_y_turn_point
        self.turn_types = turn_types
