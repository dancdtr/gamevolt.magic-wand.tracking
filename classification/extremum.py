from enum import Enum

from classification.axis import Axis


class Extremum(Enum):
    # MAX = "max"
    # MIN = "min"
    NONE = "none"
    X_MIN = "x_min"
    X_MAX = "x_max"
    Y_MIN = "y_min"
    Y_MAX = "y_max"

    # axis predicates
    def is_x(self) -> bool:
        T = type(self)
        return self is T.X_MIN or self is T.X_MAX

    def is_y(self) -> bool:
        T = type(self)
        return self is T.Y_MIN or self is T.Y_MAX

    # min/max predicates
    def is_min(self) -> bool:
        T = type(self)
        return self is T.X_MIN or self is T.Y_MIN

    def is_max(self) -> bool:
        T = type(self)
        return self is T.X_MAX or self is T.Y_MAX

    # (optional) axis property for convenience
    @property
    def axis(self) -> Axis:
        return Axis.X if self.is_x() else Axis.Y
