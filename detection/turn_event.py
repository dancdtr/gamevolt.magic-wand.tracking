from __future__ import annotations

from dataclasses import dataclass

from detection.turn import TurnType


@dataclass(frozen=True, slots=True)
class TurnEvent:
    t_ms: int  # exact timestamp (ms)
    type: TurnType
