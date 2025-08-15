from enum import Enum, auto


class TurnType(Enum):
    RIGHT_TO_LEFT = auto()  # valley in X-position (moving left → right)
    LEFT_TO_RIGHT = auto()  # peak in X-position  (right → left)
    UP_TO_DOWN = auto()  # valley in Y-position (down → up)
    DOWN_TO_UP = auto()  # peak in Y-position  (up → down)
