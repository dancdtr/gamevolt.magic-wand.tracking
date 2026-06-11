"""Windows the raw rotation stream into candidate strokes for $1 matching.

A stroke opens when motion enters MOVING and closes only on a *sustained* still phase
(HOLDING / STOPPED). A brief PAUSED (a corner / mid-spell hesitation) does NOT end the
stroke, so multi-segment glyphs arrive as one candidate. The phase tiers already encode
this: min_paused_duration < min_holding_duration, so PAUSED = transient, HOLDING =
deliberate end. Points are the running integral of the per-sample forward-vector deltas
(x_delta, y_delta) — the same 2D path used for the trail.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from gamevolt.events.event import Event
from motion.motion_phase_type import MotionPhaseType
from wand.wand_rotation import WandRotation

Point = tuple[float, float]


@dataclass(frozen=True)
class Stroke:
    points: list[Point]
    times_ms: list[int]  # aligned 1:1 with points; enables cadence / tempo scoring
    path_length: float

    @property
    def point_count(self) -> int:
        return len(self.points)

    @property
    def start_ts_ms(self) -> int:
        return self.times_ms[0] if self.times_ms else 0

    @property
    def end_ts_ms(self) -> int:
        return self.times_ms[-1] if self.times_ms else 0

    @property
    def duration_s(self) -> float:
        return max((self.end_ts_ms - self.start_ts_ms) / 1000.0, 0.0)


class StrokeWindower:
    def __init__(self, min_points: int = 8) -> None:
        self._min_points = min_points

        self._open = False
        self._points: list[Point] = []
        self._times: list[int] = []
        self._x = 0.0
        self._y = 0.0

        self.stroke_completed: Event[Callable[[Stroke], None]] = Event()

    def on_rotation(self, rotation: WandRotation) -> None:
        if not self._open:
            return
        self._x += rotation.x_delta
        self._y += rotation.y_delta
        self._points.append((self._x, self._y))
        self._times.append(rotation.ts_ms)

    def on_phase(self, phase: MotionPhaseType) -> None:
        if phase is MotionPhaseType.MOVING:
            if not self._open:
                self._open_stroke()
        elif phase in (MotionPhaseType.HOLDING, MotionPhaseType.STOPPED):
            # Sustained still = deliberate end-of-spell. A transient PAUSED is left to ride
            # so a glyph with internal hesitations stays one stroke.
            if self._open:
                self._finish()

    def reset(self) -> None:
        self._open = False
        self._points = []
        self._times = []
        self._x = 0.0
        self._y = 0.0

    def _open_stroke(self) -> None:
        self._open = True
        self._points = []
        self._times = []
        self._x = 0.0
        self._y = 0.0

    def _finish(self) -> None:
        self._open = False
        points = self._points
        times = self._times
        self._points = []
        self._times = []
        if len(points) < self._min_points:
            return

        path_length = sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)))
        self.stroke_completed.invoke(Stroke(points=points, times_ms=times, path_length=path_length))
