from collections.abc import Callable
from enum import Enum, auto
from math import sqrt

from classification.extremum import Extremum as E
from classification.gesture_classifier_mask import GestureClassifierMask
from classification.gesture_type import GestureType as G
from detection.gesture import Gesture
from detection.turn import TurnType
from detection.turn_point import TurnPoint


class Azimuth(Enum):
    N = auto()
    E = auto()
    S = auto()
    W = auto()
    NE = auto()
    SE = auto()
    SW = auto()
    NW = auto()
    NNE = auto()
    ENE = auto()
    ESE = auto()
    SSE = auto()
    SSW = auto()
    WSW = auto()
    WNW = auto()
    NNW = auto()


azimuth_angles: dict[Azimuth, float] = {
    Azimuth.N: 0,
    Azimuth.E: 90,
    Azimuth.S: 180,
    Azimuth.W: 270,
    Azimuth.NE: 45,
    Azimuth.SE: 135,
    Azimuth.SW: 225,
    Azimuth.NW: 315,
    Azimuth.NNE: 22.5,
    Azimuth.ENE: 67.5,
    Azimuth.ESE: 112.5,
    Azimuth.SSE: 157.5,
    Azimuth.SSW: 202.5,
    Azimuth.WSW: 247.5,
    Azimuth.WNW: 292.5,
    Azimuth.NNW: 337.5,
}


class GestureClassifier:
    def __init__(self) -> None:
        self._classifiers: dict[G, Callable[[Gesture], bool]] = {
            G.UP: self._is_up,
            G.RIGHT: self._is_right,
            G.DOWN: self._is_down,
            G.LEFT: self._is_left,
            G.UP_RIGHT: self._is_up_right,
            G.DOWN_RIGHT: self._is_down_right,
            G.DOWN_LEFT: self._is_down_left,
            G.UP_LEFT: self._is_up_left,
            G.UP_VIA_RIGHT_SEMI: self._is_up_via_right_semi,
            G.UP_VIA_LEFT_SEMI: self._is_up_via_left_semi,
            G.DOWN_VIA_RIGHT_SEMI: self._is_down_via_right_semi,
            G.DOWN_VIA_LEFT_SEMI: self._is_down_via_left_semi,
            G.RIGHT_VIA_UP_SEMI: self._is_right_via_up_semi,
            G.LEFT_VIA_UP_SEMI: self._is_left_via_up_semi,
            G.RIGHT_VIA_DOWN_SEMI: self._is_right_via_down_semi,
            G.LEFT_VIA_DOWN_SEMI: self._is_left_via_down_semi,
            G.LEFT_START_CW_CIRCLE: self._is_left_start_cw_circle,
            G.UP_START_CW_CIRCLE: self._is_up_start_cw_circle,
            G.RIGHT_START_CW_CIRCLE: self._is_right_start_cw_circle,
            G.DOWN_START_CW_CIRCLE: self._is_down_start_cw_circle,
            G.LEFT_START_CCW_CIRCLE: self._is_left_start_ccw_circle,
            G.UP_START_CCW_CIRCLE: self._is_up_start_ccw_circle,
            G.RIGHT_START_CCW_CIRCLE: self._is_right_start_ccw_circle,
            G.DOWN_START_CCW_CIRCLE: self._is_down_start_ccw_circle,
        }

    def classify(self, gesture: Gesture, mask: GestureClassifierMask | None = None) -> G:

        print(f"Extrema: {[e.name for e in gesture.extrema]}")
        print(f"X extrema: {[e.name for e in gesture.x_extrema]}")
        print(f"Y extrema: {[e.name for e in gesture.y_extrema]}")
        print(f"Turn points: {[tp.type.name for tp in gesture.turn_points]}")

        if mask is None:
            return self._classify_any(gesture)

        for target in mask.target_gesture_types:
            classifier = self._get_classifier(target)
            if classifier(gesture):
                return target

        return G.UNKNOWN

    def _get_classifier(self, type: G):
        classifier = self._classifiers[type]
        if not classifier:
            raise Exception(f"No classifier set for {G.name}!")
        return classifier

    def _classify_any(self, gesture) -> G:
        gesture_type = G.UNKNOWN

        # check circles
        if self._is_up_start_cw_circle(gesture):
            return G.UP_START_CW_CIRCLE
        if self._is_right_start_cw_circle(gesture):
            return G.RIGHT_START_CW_CIRCLE
        if self._is_down_start_cw_circle(gesture):
            return G.DOWN_START_CW_CIRCLE
        if self._is_left_start_cw_circle(gesture):
            return G.LEFT_START_CW_CIRCLE
        if self._is_up_start_ccw_circle(gesture):
            return G.UP_START_CCW_CIRCLE
        if self._is_right_start_ccw_circle(gesture):
            return G.RIGHT_START_CCW_CIRCLE
        if self._is_down_start_ccw_circle(gesture):
            return G.DOWN_START_CCW_CIRCLE
        if self._is_left_start_ccw_circle(gesture):
            return G.LEFT_START_CCW_CIRCLE

        # check intercardinals
        # if self._is_up_right_diagonal(gesture):
        #     return G.UP_RIGHT
        # if self._is_down_right_diagonal(gesture):
        #     return G.DOWN_RIGHT
        # if self._is_down_left_diagonal(gesture):
        #     return G.DOWN_LEFT
        # if self._is_up_left_diagonal(gesture):
        #     return G.UP_LEFT

        # check subintercardinals
        if self._is_north_north_east(gesture):
            return G.NNE
        if self._is_east_north_east(gesture):
            return G.ENE
        if self._is_east_south_east(gesture):
            return G.ESE
        if self._is_south_south_east(gesture):
            return G.SSE
        if self._is_south_south_west(gesture):
            return G.SSW
        if self._is_west_south_west(gesture):
            return G.WSW
        if self._is_west_north_west(gesture):
            return G.WNW
        if self._is_north_north_west(gesture):
            return G.NNW

        # check semi circles
        # if self._is_up_via_left_semi(gesture):
        #     return G.UP_VIA_LEFT_SEMI
        # if self._is_up_via_right_semi(gesture):
        #     return G.UP_VIA_RIGHT_SEMI
        # if self._is_right_via_up_semi(gesture):
        #     return G.RIGHT_VIA_UP_SEMI
        # if self._is_right_via_down_semi(gesture):
        #     return G.RIGHT_VIA_DOWN_SEMI
        # if self._is_down_via_right_semi(gesture):
        #     return G.DOWN_VIA_RIGHT_SEMI
        # if self._is_down_via_left_semi(gesture):
        #     return G.DOWN_VIA_LEFT_SEMI
        # if self._is_left_via_up_semi(gesture):
        #     return G.LEFT_VIA_UP_SEMI
        # if self._is_left_via_down_semi(gesture):
        #     return G.LEFT_VIA_DOWN_SEMI

        # if self._is_up(gesture):
        #     return G.UP
        # if self._is_right(gesture):
        #     return G.RIGHT
        # if self._is_down(gesture):
        #     return G.DOWN
        # if self._is_left(gesture):
        #     return G.LEFT

        return gesture_type

    def _is_circle(self, gesture: Gesture, turn_types: list[TurnType]) -> bool:
        return self._is_curve(gesture, turn_types, allow_overshoot=True)

    def _is_curve(self, gesture: Gesture, turn_types: list[TurnType], allow_overshoot: bool) -> bool:
        if turn_types == gesture.turn_types:
            return True
        elif allow_overshoot:
            return turn_types[:-1] == gesture.turn_types
        return False

    def _is_up_start_cw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN])

    def _is_right_start_cw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT])

    def _is_down_start_cw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP])

    def _is_left_start_cw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT])

    def _is_up_start_ccw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN])

    def _is_right_start_ccw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT])

    def _is_down_start_ccw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP])

    def _is_left_start_ccw_circle(self, gesture: Gesture) -> bool:
        return self._is_circle(gesture, [TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT])

    def _is_up_via_right_semi(self, gesture: Gesture) -> bool:
        return self._is_up(gesture) and self._is_right_left_curve(gesture)

    def _is_up_via_left_semi(self, gesture: Gesture) -> bool:
        return self._is_up(gesture) and self._is_left_right_curve(gesture)

    def _is_right_via_up_semi(self, gesture: Gesture) -> bool:
        return self._is_right(gesture) and self._is_up_down_curve(gesture)

    def _is_right_via_down_semi(self, gesture: Gesture) -> bool:
        return self._is_right(gesture) and self._is_down_up_curve(gesture)

    def _is_down_via_right_semi(self, gesture: Gesture) -> bool:
        return self._is_down(gesture) and self._is_right_left_curve(gesture)

    def _is_down_via_left_semi(self, gesture: Gesture) -> bool:
        return self._is_down(gesture) and self._is_left_right_curve(gesture)

    def _is_left_via_up_semi(self, gesture: Gesture) -> bool:
        return self._is_left(gesture) and self._is_up_down_curve(gesture)

    def _is_left_via_down_semi(self, gesture: Gesture) -> bool:
        return self._is_left(gesture) and self._is_down_up_curve(gesture)

    def _is_up_right_diagonal(self, gesture: Gesture) -> bool:
        return self._is_up_right(gesture) and self._is_diagonal(gesture, Azimuth.NE)

    def _is_down_right_diagonal(self, gesture: Gesture) -> bool:
        return self._is_down_right(gesture) and self._is_diagonal(gesture, Azimuth.SE)

    def _is_down_left_diagonal(self, gesture: Gesture) -> bool:
        return self._is_down_left(gesture) and self._is_diagonal(gesture, Azimuth.SW)

    def _is_up_left_diagonal(self, gesture: Gesture) -> bool:
        return self._is_up_left(gesture) and self._is_diagonal(gesture, Azimuth.NW)

    def _is_north_north_east(self, gesture: Gesture) -> bool:
        return (self._is_up_right(gesture) or self._is_up(gesture)) and self._is_diagonal(gesture, Azimuth.NNE)

    def _is_east_north_east(self, gesture: Gesture) -> bool:
        return (self._is_up_right(gesture) or self._is_right(gesture)) and self._is_diagonal(gesture, Azimuth.ENE)

    def _is_east_south_east(self, gesture: Gesture) -> bool:
        return (self._is_down_right(gesture) or self._is_right(gesture)) and self._is_diagonal(gesture, Azimuth.ESE)

    def _is_south_south_east(self, gesture: Gesture) -> bool:
        return (self._is_down_right(gesture) or self._is_down(gesture)) and self._is_diagonal(gesture, Azimuth.SSE)

    def _is_south_south_west(self, gesture: Gesture) -> bool:
        return (self._is_down_left(gesture) or self._is_down(gesture)) and self._is_diagonal(gesture, Azimuth.SSW)

    def _is_west_south_west(self, gesture: Gesture) -> bool:
        return (self._is_down_left(gesture) or self._is_left(gesture)) and self._is_diagonal(gesture, Azimuth.WSW)

    def _is_west_north_west(self, gesture: Gesture) -> bool:
        return (self._is_up_left(gesture) or self._is_left(gesture)) and self._is_diagonal(gesture, Azimuth.WNW)

    def _is_north_north_west(self, gesture: Gesture) -> bool:
        return (self._is_up_left(gesture) or self._is_up(gesture)) and self._is_diagonal(gesture, Azimuth.NNW)

    def _is_diagonal(self, gesture: Gesture, azimuth: Azimuth, variance_deg: float = 22.5) -> bool:
        angle = azimuth_angles.get(azimuth)
        if angle is None:
            raise Exception(f"Azimuth '{azimuth.name}' is not defined!")

        bearing = gesture.direction.get_bearing()
        print(f"bearing: {bearing} | variance: +- {variance_deg}")
        return (angle - variance_deg) <= bearing <= (angle + variance_deg)

    def _is_up_right(self, gesture: Gesture) -> bool:
        return gesture.direction.x < 0 and gesture.direction.y < 0 and gesture.y_extrema == [E.Y_MAX] and gesture.x_extrema == [E.X_MAX]

    def _is_down_right(self, gesture: Gesture) -> bool:
        return gesture.direction.x < 0 and gesture.direction.y > 0 and gesture.y_extrema == [E.Y_MIN] and gesture.x_extrema == [E.X_MAX]

    def _is_down_left(self, gesture: Gesture) -> bool:
        return gesture.direction.x > 0 and gesture.direction.y > 0 and gesture.y_extrema == [E.Y_MIN] and gesture.x_extrema == [E.X_MIN]

    def _is_up_left(self, gesture: Gesture) -> bool:
        return gesture.direction.x > 0 and gesture.direction.y < 0 and gesture.y_extrema == [E.Y_MAX] and gesture.x_extrema == [E.X_MIN]

    def _is_up_down_curve(self, gesture: Gesture) -> bool:
        return self._is_turn_point_type(gesture.last_y_turn_point, TurnType.UP_TO_DOWN)

    def _is_down_up_curve(self, gesture: Gesture) -> bool:
        return self._is_turn_point_type(gesture.last_y_turn_point, TurnType.DOWN_TO_UP) and gesture.y_extrema == [E.Y_MIN, E.Y_MAX]

    def _is_left_right_curve(self, gesture: Gesture) -> bool:
        return self._is_turn_point_type(gesture.last_x_turn_point, TurnType.LEFT_TO_RIGHT)

    def _is_right_left_curve(self, gesture: Gesture) -> bool:
        return self._is_turn_point_type(gesture.last_x_turn_point, TurnType.RIGHT_TO_LEFT)

    def _is_turn_point_type(self, turn_point: TurnPoint | None, turn_type: TurnType) -> bool:
        return turn_point is not None and turn_point.type == turn_type

    def _is_up(self, gesture: Gesture) -> bool:
        return gesture.direction.y < 0 and gesture.direction_abs.x < gesture.direction_abs.y and gesture.y_extrema == [E.Y_MAX]

    def _is_down(self, gesture: Gesture) -> bool:
        return gesture.direction.y > 0 and gesture.direction_abs.x < gesture.direction_abs.y and gesture.y_extrema == [E.Y_MIN]

    def _is_right(self, gesture: Gesture) -> bool:
        return gesture.direction.x < 0 and gesture.direction_abs.x > gesture.direction_abs.y and gesture.x_extrema == [E.X_MAX]

    def _is_left(self, gesture: Gesture) -> bool:
        return gesture.direction.x > 0 and gesture.direction_abs.x > gesture.direction_abs.y and gesture.x_extrema == [E.X_MIN]
