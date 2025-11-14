from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WandPosition:
    ts_ms: int
    x_delta: float
    y_delta: float

    # used for debugging
    nx: float | None
    ny: float | None

    def __str__(self) -> str:
        return f"{self.ts_ms} Δ({self.x_delta:.3f}, {self.y_delta:.3f}) [{self.nx:.3f}, {self.ny:.3f}]"
