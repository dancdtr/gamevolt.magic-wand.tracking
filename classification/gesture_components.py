from __future__ import annotations

from dataclasses import dataclass

from gamevolt.maths.axis import Axis
from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.dir import Dir
from gamevolt.maths.shape import Shape
from gamevolt.maths.span import Span
from gamevolt.maths.turn import Turn


@dataclass(frozen=True)
class GestureParts:
    shape: Shape
    start: Azimuth | None = None  # for LINE/ARC/CIRCLE
    span: Span | None = None  # for ARC (and optionally CIRCLE=FULL)
    turn: Turn | None = None  # for ARC/CIRCLE
    wave_axis: Axis | None = None  # for waves
    wave_dir: Dir | None = None  # for waves

    def code(self) -> str:
        if self.shape in (Shape.LINE,):
            assert self.start is not None
            return f"LINE_{self.start.name}"
        if self.shape == Shape.CIRCLE:
            assert self.turn and self.start
            return f"CIRCLE_{self.turn.name}_START_{self.start.name}"
        if self.shape == Shape.ARC:
            assert self.span and self.turn and self.start
            return f"ARC_{self.span.name}_{self.turn.name}_START_{self.start.name}"
        if self.shape in (Shape.WAVE_SINE, Shape.WAVE_COS):
            assert self.wave_axis and self.wave_dir
            return f"{self.shape.name}_{self.wave_axis.name}_{self.wave_dir.name}"
        raise ValueError("Incomplete GestureParts")
