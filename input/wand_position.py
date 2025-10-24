from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WandPosition:
    ts_ms: int
    x_delta: float
    y_delta: float

    # optional, only used for debugging
    x: float | None = None
    y: float | None = None

    def __str__(self) -> str:
        abs_part = "" if self.x is None or self.y is None else f" [{self.x:.3f}, {self.y:.3f}]"
        return f"{self.ts_ms} Δ({self.x_delta:.4f}, {self.y_delta:.4f}){abs_part}"
