from enum import Enum, auto


class TurnType(Enum):
    RIGHT_TO_LEFT = auto()  # valley in X-position (moving left → right)
    LEFT_TO_RIGHT = auto()  # peak in X-position  (right → left)
    UP_TO_DOWN = auto()  # valley in Y-position (down → up)
    DOWN_TO_UP = auto()  # peak in Y-position  (up → down)

    # axis predicates
    def in_x(self) -> bool:
        T = type(self)
        return self is T.LEFT_TO_RIGHT or self is T.RIGHT_TO_LEFT

    def in_y(self) -> bool:
        T = type(self)
        return self is T.UP_TO_DOWN or self is T.DOWN_TO_UP
