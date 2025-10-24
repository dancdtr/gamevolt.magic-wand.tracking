from __future__ import annotations

import math
from collections import deque
from typing import Callable

from gamevolt.events.event import Event
from input.wand_position import WandPosition
from motion.direction_type import DirectionType
from motion.gesture_segment import GestureSegment


class SegmentBuilder:
    """
    Owns the active segment and emits completed segments.
    Keeps a small buffer of recent points (optional for debugging).
    """

    def __init__(self, max_points: int = 256) -> None:
        self.segment_completed: Event[Callable[[GestureSegment], None]] = Event()

        self._active = False
        self._dir: DirectionType = DirectionType.NONE
        self._start_ms = 0
        self._last_ms = 0
        self._samples = 0
        self._net_dx = 0.0
        self._net_dy = 0.0
        self._path = 0.0
        self._points: deque[WandPosition] = deque(maxlen=max_points)

    def start(self, dir_type: DirectionType, pos: WandPosition) -> None:
        self._active = True
        self._dir = dir_type
        self._start_ms = pos.ts_ms
        self._last_ms = pos.ts_ms
        self._samples = 0
        self._net_dx = 0.0
        self._net_dy = 0.0
        self._path = 0.0
        self._points.clear()
        self._points.append(pos)

    def accumulate(self, pos: WandPosition) -> None:
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
            direction_type=self._dir,
            avg_vec_x=avg_vx,
            avg_vec_y=avg_vy,
            net_dx=self._net_dx,
            net_dy=self._net_dy,
            mean_speed=mean_speed,
            path_length=self._path,
        )
        self.segment_completed.invoke(seg)
        self._active = False

    def commit(self, new_dir: DirectionType, pos: WandPosition) -> None:
        if self._active:
            self._last_ms = pos.ts_ms
            self.finish()
        self.start(new_dir, pos)

    @property
    def active(self) -> bool:
        return self._active
