"""Windows the raw rotation stream into candidate strokes for $1 matching.

A stroke opens when motion enters MOVING and closes on a *sustained* still phase
(HOLDING / STOPPED). A brief PAUSED (a corner / mid-spell hesitation) does NOT end the
stroke, so multi-segment glyphs arrive as one candidate — but it DOES emit a provisional
snapshot of the open stroke (`stroke_paused`) so the cast assembler can commit a clean
glyph early for players who never settle after casting. The phase tiers already encode
transient-vs-deliberate: min_paused_duration < min_holding_duration. Points are the
running integral of the per-sample forward-vector deltas (x_delta, y_delta) — the same
2D path used for the trail.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Callable, Sequence

from gamevolt.events.event import Event
from motion.motion_phase_type import MotionPhaseType
from motion.stroke.configuration.stroke_windower_settings import StrokeWindowerSettings
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


def _path_length(points: Sequence[Point]) -> float:
    return sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)))


def join_strokes(strokes: Sequence[Stroke]) -> Stroke:
    """Concatenate consecutive segments into one candidate stroke.

    Segments split by a HOLDING corner-pause share the same integrated coordinate frame
    (the forward interpreter only resets on STOPPED, which flushes the segment buffer),
    so plain concatenation is valid. The small positional gap across the pause is bridged
    implicitly by the path-length sum; $1's arc-length resample absorbs it.
    """
    points = [p for stroke in strokes for p in stroke.points]
    times = [t for stroke in strokes for t in stroke.times_ms]
    return Stroke(points=points, times_ms=times, path_length=_path_length(points))


class StrokeWindower:
    def __init__(self, settings: StrokeWindowerSettings) -> None:
        self._settings = settings

        self._open = False
        self._points: deque[Point] = deque()
        self._times: deque[int] = deque()
        self._x = 0.0
        self._y = 0.0

        self.stroke_completed: Event[Callable[[Stroke], None]] = Event()
        # Provisional snapshot of the still-open stroke, emitted on a transient PAUSED.
        self.stroke_paused: Event[Callable[[Stroke], None]] = Event()

    def on_rotation(self, rotation: WandRotation) -> None:
        if not self._open:
            return
        self._x += rotation.x_delta
        self._y += rotation.y_delta
        self._points.append((self._x, self._y))
        self._times.append(rotation.ts_ms)

        max_open_s = self._settings.max_open_duration_s
        if max_open_s > 0:
            cutoff = rotation.ts_ms - int(max_open_s * 1000)
            while self._times and self._times[0] < cutoff:
                self._times.popleft()
                self._points.popleft()

    def on_phase(self, phase: MotionPhaseType) -> None:
        if phase is MotionPhaseType.MOVING:
            if not self._open:
                self._open_stroke()
        elif phase is MotionPhaseType.PAUSED:
            # Transient still: the stroke rides on, but the assembler gets a look at what
            # has been drawn so far — a clean glyph can commit here without a full settle.
            if self._open and len(self._points) >= self._settings.min_points:
                self.stroke_paused.invoke(self._snapshot())
        elif phase in (MotionPhaseType.HOLDING, MotionPhaseType.STOPPED):
            # Sustained still = deliberate end-of-segment.
            if self._open:
                self._finish()

    def abort_open_stroke(self) -> None:
        """Close the open stroke without emitting it — its points were already consumed
        via a provisional (`stroke_paused`) commit."""
        self._open = False
        self._clear()

    def reset(self) -> None:
        self._open = False
        self._clear()

    def _open_stroke(self) -> None:
        self._open = True
        self._clear()

    def _clear(self) -> None:
        self._points.clear()
        self._times.clear()
        self._x = 0.0
        self._y = 0.0

    def _snapshot(self) -> Stroke:
        points = list(self._points)
        return Stroke(points=points, times_ms=list(self._times), path_length=_path_length(points))

    def _finish(self) -> None:
        self._open = False
        if len(self._points) < self._settings.min_points:
            self._clear()
            return

        stroke = self._snapshot()
        self._clear()
        self.stroke_completed.invoke(stroke)
