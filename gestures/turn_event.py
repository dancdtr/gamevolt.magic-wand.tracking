from __future__ import annotations

from dataclasses import dataclass

from gestures.turn_type import TurnType


@dataclass(frozen=True, slots=True)
class TurnEvent:
    t_ms: int  # exact timestamp (ms)
    turn_type: TurnType
