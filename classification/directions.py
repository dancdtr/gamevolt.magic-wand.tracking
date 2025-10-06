from enum import Enum, auto

from gestures.gesture import Gesture


class CardinalDirection(Enum):
    NONE = auto()
    N = auto()
    E = auto()
    S = auto()
    W = auto()


class InterCardinalDirection(Enum):
    NONE = auto()
    N = auto()
    E = auto()
    S = auto()
    W = auto()
    NE = auto()
    SE = auto()
    SW = auto()
    NW = auto()


_MOVING_RATIO = 3


# =========================================
# General Movements
# =========================================


def get_horizontal_direction(g: Gesture) -> CardinalDirection:
    if is_moving_e(g):
        return CardinalDirection.E
    elif is_moving_w(g):
        return CardinalDirection.W
    return CardinalDirection.NONE


def get_vertical_dir(g: Gesture) -> CardinalDirection:
    if is_moving_n(g):
        return CardinalDirection.N
    elif is_moving_s(g):
        return CardinalDirection.S

    return CardinalDirection.NONE


def is_moving_ne(g: Gesture) -> bool:
    return is_moving_n(g) and is_moving_e(g)


def is_moving_se(g: Gesture) -> bool:
    return is_moving_s(g) and is_moving_e(g)


def is_moving_sw(g: Gesture) -> bool:
    return is_moving_s(g) and is_moving_w(g)


def is_moving_nw(g: Gesture) -> bool:
    return is_moving_n(g) and is_moving_w(g)


def is_moving_n(g: Gesture) -> bool:
    return g.total_velocity_n > g.total_velocity_s * _MOVING_RATIO


def is_moving_e(g: Gesture) -> bool:
    return g.total_velocity_e > g.total_velocity_w * _MOVING_RATIO


def is_moving_s(g: Gesture) -> bool:
    return g.total_velocity_s > g.total_velocity_n * _MOVING_RATIO


def is_moving_w(g: Gesture) -> bool:
    return g.total_velocity_w > g.total_velocity_e * _MOVING_RATIO


# =========================================
# Utils
# =========================================
