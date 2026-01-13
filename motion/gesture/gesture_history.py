# gesture_history.py
from __future__ import annotations

from collections import deque
from typing import Deque

from motion.gesture.configuration.gesture_history_settings import GestureHistorySettings
from motion.gesture.gesture_segment import GestureSegment


class GestureHistory:
    def __init__(self, settings: GestureHistorySettings):
        self._buf: Deque[GestureSegment] = deque(maxlen=settings.max_segments)
        self._max_age_s = settings.max_age

    def add(self, seg: GestureSegment) -> None:
        self._buf.append(seg)
        self._prune()

    def tail(self) -> list[GestureSegment]:
        """Return a snapshot list (already pruned)."""
        x = list(self._buf)

        # details = [(seg.direction_type.name.lower(), seg.duration_s, seg.path_length) for seg in x]

        # print(f"total active s: {sum([d[1] for d in details]):.2f}")
        # print(f"total distance: {sum([d[2] for d in details]):.2f}")
        # print([f"{d[0]} | {d[1]} | {d[2]:.2f}" for d in details])
        return x

    def clear(self) -> None:
        self._buf.clear()

    def _prune(self) -> None:
        if not self._buf:
            return

        now_end_ms = self._buf[-1].end_ts_ms
        cutoff_ms = now_end_ms - int(self._max_age_s * 1000)
        while self._buf and self._buf[0].end_ts_ms < cutoff_ms:
            self._buf.popleft()
