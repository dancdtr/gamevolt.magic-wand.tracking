from enum import Enum

import numpy as np

from vector_2 import Vector2


class Axis(Enum):
    X = "x"
    Y = "y"


class EXTREMA(Enum):
    MAX = "max"
    MIN = "min"


class Gesture(Enum):
    UNKNOWN = "unknown"
    UP = "up"
    RIGHT = "right"
    DOWN = "down"
    LEFT = "left"

    UP_RIGHT = "up_right"
    DOWN_RIGHT = "down_right"
    DOWN_LEFT = "down_left"
    UP_LEFT = "up_left"

    UP_RIGHT_SEMI = "up_right_semi"
    UP_LEFT_SEMI = "up_left_semi"
    DOWN_RIGHT_SEMI = "down_right_semi"
    DOWN_LEFT_SEMI = "down_left_semi"

    RIGHT_UP_SEMI = "right_up_semi"
    LEFT_UP_SEMI = "left_up_semi"
    RIGHT_DOWN_SEMI = "right_down_semi"
    LEFT_DOWN_SEMI = "left_down_semi"


type G = Gesture


class CurveClassifier:
    def __init__(self) -> None:
        self.INTERCARDINAL_RATIO = 0.65
        self.MAX_POS_FRACTION = 0.3  # peak must lie within middle 60% of stroke
        self.BASELINE_TOLERANCE = 0.3  # end y vs start y within 10% of width
        self.MAX_THRESH_FRACTION = 0.3

    def classify(self, points: list[Vector2]) -> str:
        v = Vector2.from_average(points)
        abs_x, abs_y = abs(v.x), abs(v.y)

        if abs_x and abs_y and (min(abs_x, abs_y) / max(abs_x, abs_y) >= self.INTERCARDINAL_RATIO):
            if v.x > 0 and v.y > 0:
                direction = "down-left"
            elif v.x > 0 and v.y < 0:
                direction = "up-left"
            elif v.x < 0 and v.y < 0:
                direction = "up-right"
            else:
                direction = "down-right"
        else:
            if abs_x > abs_y:
                direction = "left" if v.x > 0 else "right"
            else:
                direction = "down" if v.y > 0 else "up"

        extrema = []

        if direction == "right":
            extrema = self._squish_extrema(self._extrema_sequence(points, Axis.Y))
            print(extrema)
            if extrema == ["max", "min"]:
                return "right-up-semi"
            if extrema == ["min", "max"]:
                return "right-down-semi"

        if direction == "left":
            extrema = self._squish_extrema(self._extrema_sequence(points, Axis.Y))
            print(extrema)
            if extrema == ["max", "min"]:
                return "left-up-semi"
            if extrema == ["min", "max"]:
                return "left-down-semi"

        if direction == "up":
            extrema = self._squish_extrema(self._extrema_sequence(points, Axis.X))
            print(extrema)
            if extrema == ["max", "min"]:
                return "up-right-semi"
            if extrema == ["min", "max"]:
                return "up-left-semi"

        if direction == "down":
            extrema = self._squish_extrema(self._extrema_sequence(points, Axis.X))
            print(extrema)
            if extrema == ["max", "min"]:
                return "down-right-semi"
            if extrema == ["min", "max"]:
                return "down-left-semi"

        return direction

    def _extrema_sequence(self, points: list[Vector2], axis: Axis) -> list[str]:
        """
        Scan either the x-velocity (if x_axis=True) or y-velocity (else)
        and return the ordered list of 'max' / 'min' labels of
        significant local extrema.

        - A 'max' is a sample above both neighbors and > +thr.
        - A 'min' is a sample below both neighbors and < -thr.

        Args:
            points:  list of Vector2 (vx, vy) samples
            x_axis:  if True scan p.x; otherwise scan p.y

        Returns:
            A list like ['max', 'min', ...] in chronological order.
        """
        ps = np.array([p.x for p in points], float) if axis == Axis.X else np.array([p.y for p in points], float)

        n = len(ps)
        if n < 3:
            return []

        # threshold = fraction of the peak magnitude
        thr = self.MAX_THRESH_FRACTION * np.max(np.abs(ps))

        extrema = []
        for i in range(1, n - 1):
            previous, current, next = ps[i - 1], ps[i], ps[i + 1]
            if current > previous and current > next and current > thr:
                extrema.append((i, "min"))
            elif current < previous and current < next and current < -thr:
                extrema.append((i, "max"))

        # sort by index (they're already in order, but just in case)
        extrema.sort(key=lambda x: x[0])
        # return only the labels
        return [label for _, label in extrema]

    def _squish_extrema(self, extrema: list[str]) -> list[str]:
        if len(extrema) < 1:
            return []

        squished = [extrema[0]]
        for ex in extrema[1:]:
            if squished[-1] != ex:
                squished.append(ex)

        return squished
