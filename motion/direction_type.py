from enum import Enum, auto


class DirectionType(Enum):
    NONE = auto()
    MOVING_N = auto()
    MOVING_NE = auto()
    MOVING_E = auto()
    MOVING_SE = auto()
    MOVING_S = auto()
    MOVING_SW = auto()
    MOVING_W = auto()
    MOVING_NW = auto()
