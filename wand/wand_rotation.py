from dataclasses import dataclass


@dataclass(frozen=True)
class WandRotation:
    id: str
    ts_ms: int
    x_delta: float
    y_delta: float

    # used for debugging
    nx: float | None
    ny: float | None

    def __str__(self) -> str:
        return f"{self.id} | {self.ts_ms} Δ({self.x_delta:.3f}, {self.y_delta:.3f}) [{self.nx:.3f}, {self.ny:.3f}]"
