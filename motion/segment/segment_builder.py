from __future__ import annotations

import math
from collections import deque
from typing import Callable, Deque

from gamevolt.events.event import Event
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from motion.segment.configuration.segment_builder_settings import SegmentBuilderSettings
from wand.wand_rotation import WandRotation


class SegmentBuilder:
    """
    Owns the active segment and emits completed segments.

    Semantics:
      - A segment starts with `start(dir_type, pos)`.
      - Each subsequent `accumulate(pos)` adds deltas (dx, dy) and length to the
        active segment.
      - `commit(new_dir, pos)` closes the current segment (if any) using `pos`
        as the end timestamp, emits it, then starts a new segment at `pos`
        with the given `new_dir`.
      - `finish()` closes the active segment (if any) without starting a new one.

    The `sample_count` in GestureSegment counts the number of accumulated
    motion samples (deltas), not the number of WandPosition points.
    """

    def __init__(self, settings: SegmentBuilderSettings) -> None:
        self._settings = settings

        self._active: bool = False
        self._direction: DirectionType = DirectionType.NONE
        self._start_ms: int = 0
        self._last_ms: int = 0
        self._samples: int = 0
        self._net_dx: float = 0.0
        self._net_dy: float = 0.0
        self._path: float = 0.0
        self._points: Deque[WandRotation] = deque(maxlen=settings.max_sample_count)

        self.segment_completed: Event[Callable[[GestureSegment], None]] = Event()

    @property
    def active(self) -> bool:
        return self._active

    def start(self, dir_type: DirectionType, pos: WandRotation) -> None:
        self._active = True
        self._direction = dir_type
        self._start_ms = pos.ts_ms
        self._last_ms = pos.ts_ms
        self._samples = 0
        self._net_dx = 0.0
        self._net_dy = 0.0
        self._path = 0.0
        self._points.clear()
        self._points.append(pos)

    def accumulate(self, pos: WandRotation) -> None:
        if not self._active:
            return

        self._last_ms = pos.ts_ms
        dx = pos.x_delta
        dy = pos.y_delta
        self._net_dx += dx
        self._net_dy += dy
        self._path += math.hypot(dx, dy)
        self._samples += 1
        self._points.append(pos)

    def finish(self) -> None:
        if not self._active:
            return

        duration_s = max((self._last_ms - self._start_ms) / 1000.0, 0.0)
        mag = math.hypot(self._net_dx, self._net_dy)
        avg_vx = (self._net_dx / mag) if mag > 0 else 0.0
        avg_vy = (self._net_dy / mag) if mag > 0 else 0.0
        mean_speed = (self._path / duration_s) if duration_s > 0 else 0.0

        seg = GestureSegment(
            start_ts_ms=self._start_ms,
            end_ts_ms=self._last_ms,
            duration_s=duration_s,
            sample_count=self._samples,
            direction_type=self._direction,
            avg_vec_x=avg_vx,
            avg_vec_y=avg_vy,
            net_dx=self._net_dx,
            net_dy=self._net_dy,
            mean_speed=mean_speed,
            path_length=self._path,
        )

        self._active = False
        self.segment_completed.invoke(seg)

    def commit(self, new_dir: DirectionType, pos: WandRotation) -> None:
        if self._active:
            self._last_ms = pos.ts_ms
            self.finish()
        self.start(new_dir, pos)

    def reset(self) -> None:
        self._active = False
        self._direction = DirectionType.NONE
        self._start_ms = 0
        self._last_ms = 0
        self._samples = 0
        self._net_dx = 0.0
        self._net_dy = 0.0
        self._path = 0.0
        self._points.clear()
