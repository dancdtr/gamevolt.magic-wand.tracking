from __future__ import annotations

from collections import deque
from typing import Deque, Iterable, Sequence

from input.wand_position import WandPosition
from visualisation.configuration.trail_settings import TrailSettings


class Trail:
    def __init__(self, settings: TrailSettings) -> None:
        self._points: Deque[tuple[float, float]] = deque(maxlen=settings.max_points)

    @property
    def max_points(self) -> int:
        return self._points.maxlen or 0

    def __len__(self) -> int:
        return len(self._points)

    def clear(self) -> None:
        self._points.clear()

    def add_xy(self, x: float, y: float) -> None:
        self._points.append((x, y))

    def add(self, pos: WandPosition) -> None:
        if pos.nx and pos.ny:
            self.add_xy(pos.nx, pos.ny)

    def extend_xy(self, pts: Iterable[tuple[float, float]]) -> None:
        for x, y in pts:
            self._points.append((x, y))

    def points(self) -> Sequence[tuple[float, float]]:
        # Return a stable snapshot; still cheap for UI usage
        return list(self._points)
