# gesture_history.py
from __future__ import annotations

from collections import deque
from typing import Deque

from motion.gesture_segment import GestureSegment


class GestureHistory:
    """Rolling store of recent segments, pruned by age and length."""

    def __init__(self, max_segments: int = 200, max_age_s: float = 4.0):
        self._buf: Deque[GestureSegment] = deque(maxlen=max_segments)
        self._max_age_s = max_age_s

    def add(self, seg: GestureSegment) -> None:
        self._buf.append(seg)
        self._prune()

    def tail(self) -> list[GestureSegment]:
        """Return a snapshot list (already pruned)."""
        return list(self._buf)

    def clear(self) -> None:
        self._buf.clear()

    def _prune(self) -> None:
        if not self._buf:
            return

        now_end_ms = self._buf[-1].end_ts_ms
        cutoff_ms = now_end_ms - int(self._max_age_s * 1000)
        while self._buf and self._buf[0].end_ts_ms < cutoff_ms:
            self._buf.popleft()
