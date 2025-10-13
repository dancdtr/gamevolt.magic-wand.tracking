from dataclasses import dataclass

from motion.direction_type import DirectionType


@dataclass
class Gesture:
    motion: DirectionType
    start_ts: int
    end_ts: int | None = None
