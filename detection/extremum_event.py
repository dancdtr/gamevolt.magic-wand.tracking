from __future__ import annotations

from dataclasses import dataclass

from gamevolt.maths.extremum import Extremum


@dataclass(frozen=True, slots=True)
class ExtremumEvent:
    t_ms: int
    type: Extremum  # e.g., Extremum.X_MAX
    value: float
