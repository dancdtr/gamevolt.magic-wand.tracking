from dataclasses import dataclass


@dataclass(frozen=True)
class WandPosition:
    ts_ms: int
    x: float
    y: float

    def __str__(self) -> str:
        return f"{self.ts_ms} ({self.x:.3f}, {self.y:.3f})"
