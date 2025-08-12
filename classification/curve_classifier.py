import numpy as np

from classification.axis import Axis
from classification.extrema import Extrema as E
from classification.gesture_type import GestureType as G
from vector_2 import Vector2


class CurveClassifier:
    def __init__(self, intercardinal_ratio=0.8, extrema_thresh_faction=0.65, extrema_window: int = 3) -> None:
        self._intercardinal_ratio = intercardinal_ratio
        self._extrema_thresh_fraction = extrema_thresh_faction
        self._extrema_window = max(1, extrema_window)

    def classify(self, points: list[Vector2]) -> G:
        v = Vector2.from_average(points)
        abs_x, abs_y = abs(v.x), abs(v.y)

        # 1) Determine base gesture
        if abs_x and abs_y and (min(abs_x, abs_y) / max(abs_x, abs_y) >= self._intercardinal_ratio):
            if v.x > 0 and v.y > 0:
                gesture = G.DOWN_LEFT
            elif v.x > 0 and v.y < 0:
                gesture = G.UP_LEFT
            elif v.x < 0 and v.y < 0:
                gesture = G.UP_RIGHT
            else:
                gesture = G.DOWN_RIGHT
        else:
            if abs_x > abs_y:
                gesture = G.LEFT if v.x > 0 else G.RIGHT
            else:
                gesture = G.DOWN if v.y > 0 else G.UP

        # 2) Check for semi-circle via extrema on secondary axis
        if gesture in (G.RIGHT, G.LEFT):
            extrema = self._squish_extrema(self._extrema_sequence(points, Axis.Y))
            self._print_extrema(extrema)
            if extrema == [E.MAX, E.MIN]:
                return G.RIGHT_UP_SEMI if gesture == G.RIGHT else G.LEFT_UP_SEMI
            if extrema == [E.MIN, E.MAX]:
                return G.RIGHT_DOWN_SEMI if gesture == G.RIGHT else G.LEFT_DOWN_SEMI

        if gesture in (G.UP, G.DOWN):
            extrema = self._squish_extrema(self._extrema_sequence(points, Axis.X))
            self._print_extrema(extrema)
            if extrema == [E.MAX, E.MIN]:
                return G.UP_RIGHT_SEMI if gesture == G.UP else G.DOWN_RIGHT_SEMI
            if extrema == [E.MIN, E.MAX]:
                return G.UP_LEFT_SEMI if gesture == G.UP else G.DOWN_LEFT_SEMI

        return gesture

    def _extrema_sequence(self, points: list[Vector2], axis: Axis) -> list[E]:
        """
        Scan velocities along the given axis and return ordered list of
        local extrema E.MAX/E.MIN by comparing each sample to a neighborhood.
        """
        n = len(points)
        if n < 2 * self._extrema_window + 1:
            return []

        # extract velocity array
        vals = np.array([p.x for p in points], float) if axis == Axis.X else np.array([p.y for p in points], float)
        thr = self._extrema_thresh_fraction * np.max(np.abs(vals))

        extrema = []
        w = self._extrema_window
        # slide window, skip edges
        for i in range(w, n - w):
            window_vals = vals[i - w : i + w + 1]
            cur = vals[i]
            # local maximum in window
            if cur == window_vals.max() and cur > thr:
                extrema.append((i, E.MIN))
            # local minimum in window
            elif cur == window_vals.min() and cur < -thr:
                extrema.append((i, E.MAX))

        extrema.sort(key=lambda x: x[0])
        return [label for _, label in extrema]

    def _squish_extrema(self, extrema: list[E]) -> list[E]:
        """Remove consecutive duplicates in extrema list."""
        if not extrema:
            return []
        squished = [extrema[0]]
        for e in extrema[1:]:
            if e != squished[-1]:
                squished.append(e)
        return squished

    def _print_extrema(self, extrema: list[E]) -> None:
        names = [e.name for e in extrema]
        print(f"Extrema: {names}")
