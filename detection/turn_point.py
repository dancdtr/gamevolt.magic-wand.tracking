from typing import NamedTuple

from detection.turn import TurnType


class TurnPoint(NamedTuple):
    idx: float  # fractional index (interpolated)
    t_ms: float  # interpolated timestamp
    type: TurnType
