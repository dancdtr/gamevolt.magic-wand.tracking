import numpy as np

from detection.configuration.gesture_settings import GestureSettings
from detection.extremum_event import ExtremumEvent
from gamevolt.maths.extremum import Extremum
from gamevolt.maths.vector_2 import Vector2
from gestures.gesture import Gesture
from gestures.gesture_point import GesturePoint
from gestures.turn_event import TurnEvent
from gestures.turn_type import TurnType


class GestureFactory:
    def __init__(self, settings: GestureSettings) -> None:
        self._settings = settings

    def create(self, gesture_points: list[GesturePoint]) -> Gesture:
        if len(gesture_points) < self._settings.min_sample:
            raise ValueError("not enough samples")

        points = [g.velocity for g in gesture_points]

        duration = gesture_points[-1].timestamp - gesture_points[0].timestamp

        # onset_k = min(self._settings.start_frames, len(points))
        # onset_vec = Vector2.from_average(points[:onset_k])
        # normalize safely
        # mag = max(abs(onset_vec.x), abs(onset_vec.y), 1e-9)
        # onset_heading = Vector2(onset_vec.x / mag, onset_vec.y / mag)

        # earliest reliable extremum (edge-aware)
        # first_idx, first_ext = self._first_extremum(points)

        # full extrema sequence (for later analyzers)
        extrema = self._get_extrema_sequence(gesture_points)

        # direction = Vector2.from_average(points)

        timestamps = [gp.timestamp for gp in gesture_points]
        turn_points = self._get_velocity_turn_points(points, timestamps)

        # You can either extend Gesture to carry these, or stash in a metadata dict
        return Gesture(
            points=gesture_points,
            duration=duration,
            extrema_events=extrema,
            turn_events=turn_points,
        )

    def _get_extrema_sequence(self, points: list[GesturePoint]) -> list[ExtremumEvent]:
        """
        Slide a window and emit axis-tagged extrema where the CENTER sample
        is the unique (or first) max/min and clears a threshold.
        """
        n = len(points)
        w = self._settings.extrema_window
        if n < 2 * w + 1:
            return []

        x_vals = np.array([p.velocity.x for p in points], dtype=float)
        y_vals = np.array([p.velocity.y for p in points], dtype=float)
        t_s = np.array([p.timestamp for p in points], dtype=float)

        x_abs_max = np.max(np.abs(x_vals))
        y_abs_max = np.max(np.abs(y_vals))
        if x_abs_max == 0 and y_abs_max == 0:
            return []

        x_thr = self._settings.extrema_thresh_fraction * x_abs_max if x_abs_max > 0 else float("inf")
        y_thr = self._settings.extrema_thresh_fraction * y_abs_max if y_abs_max > 0 else float("inf")

        events: list[ExtremumEvent] = []

        center = w  # index of the center inside each window
        for i in range(w, n - w):
            x_win = x_vals[i - w : i + w + 1]
            y_win = y_vals[i - w : i + w + 1]

            # X axis: require the center to be the (first) argmax/argmin
            if np.argmax(x_win) == center and x_vals[i] > x_thr:
                events.append(ExtremumEvent(t_s[i], Extremum.X_MIN, x_vals[i]))
            elif np.argmin(x_win) == center and x_vals[i] < -x_thr:
                events.append(ExtremumEvent(t_s[i], Extremum.X_MAX, x_vals[i]))

            # Y axis
            if np.argmax(y_win) == center and y_vals[i] > y_thr:
                events.append(ExtremumEvent(t_s[i], Extremum.Y_MIN, y_vals[i]))
            elif np.argmin(y_win) == center and y_vals[i] < -y_thr:
                events.append(ExtremumEvent(t_s[i], Extremum.Y_MAX, y_vals[i]))

        return self._squish(events)

    def _squish(self, extrema_events: list[ExtremumEvent]) -> list[ExtremumEvent]:
        # Drop consecutive duplicates per axis
        prev_x = Extremum.NONE
        prev_y = Extremum.NONE
        squished: list[ExtremumEvent] = []

        for e in extrema_events:
            if e.type in (Extremum.X_MIN, Extremum.X_MAX):
                if e.type != prev_x:
                    squished.append(e)
                    prev_x = e.type
            else:  # Y_MIN/Y_MAX
                if e.type != prev_y:
                    squished.append(e)
                    prev_y = e.type
        return squished

    def _first_extremum(self, points: list[Vector2]) -> tuple[int | None, Extremum]:
        """
        Find the first local extremum with an edge-aware window.
        Returns (index, label) in gesture-local indices.
        """
        n = len(points)
        if n < 3:
            return (None, Extremum.NONE)

        w = self._settings.extrema_window
        x = np.array([p.x for p in points], float)
        y = np.array([p.y for p in points], float)

        x_abs = np.max(np.abs(x))
        y_abs = np.max(np.abs(y))
        if x_abs == 0 and y_abs == 0:
            return (None, Extremum.NONE)

        x_thr = self._settings.extrema_thresh_fraction * x_abs if x_abs > 0 else float("inf")
        y_thr = self._settings.extrema_thresh_fraction * y_abs if y_abs > 0 else float("inf")

        # search early region first so you anchor near the start
        early_end = min(n, max(3, 3 * w))

        for i in range(1, early_end - 1):
            # dynamic, edge-aware neighborhood
            i0 = max(0, i - w)
            i1 = min(n, i + w + 1)

            x_win = x[i0:i1]
            y_win = y[i0:i1]
            cx = i - i0  # center index inside the window
            cy = cx

            # X axis
            if np.argmax(x_win) == cx and x[i] > x_thr:
                return (i, Extremum.X_MAX)
            if np.argmin(x_win) == cx and x[i] < -x_thr:
                return (i, Extremum.X_MIN)

            # Y axis
            if np.argmax(y_win) == cy and y[i] > y_thr:
                return (i, Extremum.Y_MAX)
            if np.argmin(y_win) == cy and y[i] < -y_thr:
                return (i, Extremum.Y_MIN)

        return (None, Extremum.NONE)

    def _get_velocity_turn_points(
        self,
        points,
        timestamps_ms,
        *,
        zero_frac: float = 0.25,
        hysteresis_ratio: float = 0.5,
        min_gap_ms: float = 12.0,
        dwell_frames: int = 0,
        adaptive: bool = True,
        decay: float = 0.995,  # <-- new
    ):
        n = len(points)
        if n < 2 or len(timestamps_ms) != n:
            return []

        x = np.fromiter((p.x for p in points), float, count=n)
        y = np.fromiter((p.y for p in points), float, count=n)
        t = np.asarray(timestamps_ms, dtype=float)

        def detect_axis(v: np.ndarray, axis: str):
            if np.all(v == 0.0):
                return []

            # optional light smoothing (helps jitter). comment out if not needed.
            v = np.convolve(v, np.ones(3) / 3, mode="same")

            vmax = float(np.max(np.abs(v)))
            peak = max(vmax, 1e-9)  # init peak
            state = 0  # -1,0,+1
            last_nz_sign = 0
            last_nz_i = None
            last_emit_t = -1e18
            run_len = 0
            out: list[TurnEvent] = []

            for i in range(n):
                # update adaptive amplitude
                if adaptive:
                    peak = max(abs(v[i]), peak * decay)
                else:
                    peak = vmax

                eps_enter = zero_frac * peak
                eps_exit = hysteresis_ratio * eps_enter

                # hysteretic sign state
                val = float(v[i])
                if state >= 0 and val > +eps_enter:
                    state = +1
                elif state <= 0 and val < -eps_enter:
                    state = -1
                elif abs(val) < eps_exit:
                    state = 0
                # else: hold

                sign = 1 if state > 0 else (-1 if state < 0 else 0)

                # stability run (optional)
                if sign != 0:
                    run_len = run_len + 1 if (last_nz_sign == sign) else 1
                else:
                    run_len = 0

                # crossing when new non-zero sign != last non-zero sign
                if sign != 0 and last_nz_sign != 0 and sign != last_nz_sign and last_nz_i is not None:
                    j = last_nz_i
                    v0, v1 = float(v[j]), float(v[i])
                    t0, t1 = float(t[j]), float(t[i])
                    t0, t1 = float(t[j]), float(t[i])
                    denom = v1 - v0
                    alpha = -v0 / denom if abs(denom) > 1e-12 else 0.5
                    if alpha < 0.0:
                        alpha = 0.0
                    elif alpha > 1.0:
                        alpha = 1.0
                    z_t = t0 + alpha * (t1 - t0)
                    if (z_t - last_emit_t) >= min_gap_ms:
                        label = (
                            TurnType.W2E
                            if (axis == "x" and sign < 0)
                            else (
                                TurnType.E2W if (axis == "x" and sign > 0) else TurnType.S2N if (axis == "y" and sign < 0) else TurnType.N2S
                            )
                        )
                        # z_idx = j + alpha * (i - j)
                        # out.append(TurnEvent(z_idx, z_t, label))
                        out.append(TurnEvent(t_ms=t[j], turn_type=label))
                        last_emit_t = z_t

                # commit last non-zero anchor (with optional dwell)
                if sign != 0 and (dwell_frames == 0 or run_len >= dwell_frames):
                    last_nz_sign = sign
                    last_nz_i = i

            return out

        turns = detect_axis(x, "x") + detect_axis(y, "y")
        # turns.sort(key=lambda tp: (tp.t_ms, tp.idx))
        turns.sort(key=lambda tp: (tp.t_ms))
        return turns
