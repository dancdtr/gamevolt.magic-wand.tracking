from classification.extremum import Extremum as E
from classification.gesture_type import GestureType as G
from detection.gesture import Gesture


class CurveClassifier:
    def __init__(self, intercardinal_ratio=0.8) -> None:
        self._intercardinal_ratio = intercardinal_ratio

    def classify(self, gesture: Gesture) -> G:

        print(f"Extrema: {[e.name for e in gesture.extrema]}")
        print(f"X extrema: {[e.name for e in gesture.x_extrema]}")
        print(f"Y extrema: {[e.name for e in gesture.y_extrema]}")

        gesture_type = G.UNKNOWN

        # 2) Check for circle:

        if gesture.extrema == [E.Y_MAX, E.X_MAX, E.Y_MIN, E.X_MIN]:
            return G.LEFT_START_CW_CIRCLE
        if gesture.extrema == [E.X_MAX, E.Y_MIN, E.X_MIN, E.Y_MAX]:
            return G.UP_START_CW_CIRCLE
        if gesture.extrema == [E.Y_MIN, E.X_MIN, E.Y_MAX, E.X_MAX]:
            return G.RIGHT_START_CW_CIRCLE
        if gesture.extrema == [E.X_MIN, E.Y_MAX, E.X_MAX, E.Y_MIN]:
            return G.DOWN_START_CW_CIRCLE

        if gesture.extrema == [E.Y_MIN, E.X_MAX, E.Y_MAX, E.X_MIN]:
            return G.LEFT_START_CCW_CIRCLE
        if gesture.extrema == [E.X_MIN, E.Y_MAX, E.X_MAX, E.Y_MIN]:
            return G.UP_START_CCW_CIRCLE
        if gesture.extrema == [E.Y_MAX, E.X_MIN, E.Y_MIN, E.X_MAX]:
            return G.RIGHT_START_CCW_CIRCLE
        if gesture.extrema == [E.X_MAX, E.Y_MIN, E.X_MIN, E.Y_MAX]:
            return G.DOWN_START_CCW_CIRCLE

        # check diagonals
        if self._is_up_right_diagonal(gesture):
            return G.UP_RIGHT
        if self._is_down_right_diagonal(gesture):
            return G.DOWN_RIGHT
        if self._is_down_left_diagonal(gesture):
            return G.DOWN_LEFT
        if self._is_up_left_diagonal(gesture):
            return G.UP_LEFT

        # check semi circles
        if self._is_up_via_left_semi(gesture):
            return G.UP_VIA_LEFT_SEMI
        if self._is_up_via_right_semi(gesture):
            return G.UP_VIA_RIGHT_SEMI
        if self._is_right_via_up_semi(gesture):
            return G.RIGHT_VIA_UP_SEMI
        if self._is_right_via_down_semi(gesture):
            return G.RIGHT_VIA_DOWN_SEMI
        if self._is_down_via_right_semi(gesture):
            return G.DOWN_VIA_RIGHT_SEMI
        if self._is_down_via_left_semi(gesture):
            return G.DOWN_VIA_LEFT_SEMI
        if self._is_left_via_up_semi(gesture):
            return G.LEFT_VIA_UP_SEMI
        if self._is_left_via_down_semi(gesture):
            return G.LEFT_VIA_DOWN_SEMI

        return gesture_type

    def _is_up_via_right_semi(self, gesture: Gesture) -> bool:
        return self._is_up(gesture) and self._is_right_left(gesture)

    def _is_up_via_left_semi(self, gesture: Gesture) -> bool:
        return self._is_up(gesture) and self._is_left_right(gesture)

    def _is_right_via_up_semi(self, gesture: Gesture) -> bool:
        return self._is_right(gesture) and self._is_up_down(gesture)

    def _is_right_via_down_semi(self, gesture: Gesture) -> bool:
        return self._is_right(gesture) and self._is_down_up(gesture)

    def _is_down_via_right_semi(self, gesture: Gesture) -> bool:
        return self._is_down(gesture) and self._is_right_left(gesture)

    def _is_down_via_left_semi(self, gesture: Gesture) -> bool:
        return self._is_down(gesture) and self._is_left_right(gesture)

    def _is_left_via_up_semi(self, gesture: Gesture) -> bool:
        return self._is_left(gesture) and self._is_up_down(gesture)

    def _is_left_via_down_semi(self, gesture: Gesture) -> bool:
        return self._is_left(gesture) and self._is_down_up(gesture)

    def _is_up_right_diagonal(self, gesture: Gesture) -> bool:
        return self._is_up_right(gesture) and self._is_diagonal(gesture)

    def _is_down_right_diagonal(self, gesture: Gesture) -> bool:
        return self._is_down_right(gesture) and self._is_diagonal(gesture)

    def _is_down_left_diagonal(self, gesture: Gesture) -> bool:
        return self._is_down_left(gesture) and self._is_diagonal(gesture)

    def _is_up_left_diagonal(self, gesture: Gesture) -> bool:
        return self._is_up_left(gesture) and self._is_diagonal(gesture)

    def _is_up(self, gesture: Gesture) -> bool:
        return gesture.direction.y < 0 and gesture.direction_abs.x < gesture.direction_abs.y and gesture.y_extrema == [E.Y_MAX]

    def _is_down(self, gesture: Gesture) -> bool:
        return gesture.direction.y > 0 and gesture.direction_abs.x < gesture.direction_abs.y and gesture.y_extrema == [E.Y_MIN]

    def _is_right(self, gesture: Gesture) -> bool:
        return gesture.direction.x < 0 and gesture.direction_abs.x > gesture.direction_abs.y and gesture.x_extrema == [E.X_MAX]

    def _is_left(self, gesture: Gesture) -> bool:
        return gesture.direction.x > 0 and gesture.direction_abs.x > gesture.direction_abs.y and gesture.x_extrema == [E.X_MIN]

    def _is_diagonal(self, gesture: Gesture) -> bool:
        return gesture.min_direction_abs / gesture.max_direction_abs >= self._intercardinal_ratio

    def _is_up_right(self, gesture: Gesture) -> bool:
        return gesture.direction.x < 0 and gesture.direction.y < 0 and gesture.y_extrema == [E.Y_MAX] and gesture.x_extrema == [E.X_MAX]

    def _is_down_right(self, gesture: Gesture) -> bool:
        return gesture.direction.x < 0 and gesture.direction.y > 0 and gesture.y_extrema == [E.Y_MIN] and gesture.x_extrema == [E.X_MAX]

    def _is_down_left(self, gesture: Gesture) -> bool:
        return gesture.direction.x > 0 and gesture.direction.y > 0 and gesture.y_extrema == [E.Y_MIN] and gesture.x_extrema == [E.X_MIN]

    def _is_up_left(self, gesture: Gesture) -> bool:
        return gesture.direction.x > 0 and gesture.direction.y < 0 and gesture.y_extrema == [E.Y_MAX] and gesture.x_extrema == [E.X_MIN]

    def _is_up_down(self, gesture: Gesture) -> bool:
        return gesture.y_extrema == [E.Y_MAX, E.Y_MIN]

    def _is_down_up(self, gesture: Gesture) -> bool:
        return gesture.y_extrema == [E.Y_MIN, E.Y_MAX]

    def _is_left_right(self, gesture: Gesture) -> bool:
        return gesture.x_extrema == [E.X_MIN, E.X_MAX]

    def _is_right_left(self, gesture: Gesture) -> bool:
        return gesture.x_extrema == [E.X_MAX, E.X_MIN]
