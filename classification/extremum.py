from __future__ import annotations

from enum import Enum

from classification.axis import Axis
from classification.azimuth import Azimuth


class Extremum(Enum):
    NONE = "none"
    X_MIN = "x_min"
    X_MAX = "x_max"
    Y_MIN = "y_min"
    Y_MAX = "y_max"

    def is_x(self) -> bool:
        T = type(self)
        return self is T.X_MIN or self is T.X_MAX

    def is_y(self) -> bool:
        T = type(self)
        return self is T.Y_MIN or self is T.Y_MAX

    def is_min(self) -> bool:
        T = type(self)
        return self is T.X_MIN or self is T.Y_MIN

    def is_max(self) -> bool:
        T = type(self)
        return self is T.X_MAX or self is T.Y_MAX

    @property
    def axis(self) -> Axis:
        return Axis.X if self.is_x() else Axis.Y

    @staticmethod
    def from_azimuth(az: Azimuth) -> Extremum:
        match az:
            case Azimuth.N: return Extremum.Y_MAX
            case Azimuth.E: return Extremum.X_MAX
            case Azimuth.S: return Extremum.Y_MIN
            case Azimuth.W: return Extremum.X_MIN
            case _: raise ValueError(f"No Extremum defined for {az.name}.")
