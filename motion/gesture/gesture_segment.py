# gesture_segment.py
from __future__ import annotations

from dataclasses import dataclass
from math import atan2

from motion.direction.direction_type import DirectionType


@dataclass(frozen=True)
class GestureSegment:
    start_ts_ms: int
    end_ts_ms: int
    duration_s: float

    sample_count: int
    direction_type: DirectionType
    avg_vec_x: float
    avg_vec_y: float
    net_dx: float
    net_dy: float
    mean_speed: float
    path_length: float

    @property
    def direction(self) -> float:
        x = atan2(self.avg_vec_y, self.avg_vec_x) * 180 / 3.142
        if x > 0:
            return x + 90

        return x
