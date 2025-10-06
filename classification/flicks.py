from enum import Enum, auto

from classification.directions import CardinalDirection, is_moving_ne, is_moving_nw, is_moving_se, is_moving_sw
from gestures.gesture import Gesture

_FLICK_RATIO = 1.2
_SPLIT_POSITION = 0.5


class Rotation(Enum):
    NONE = auto()
    CW = auto()
    CCW = auto()


# =========================================
# Flicks CW
# =========================================


def is_flick_cw_ne(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.N, CardinalDirection.E) and is_moving_ne(g)


def is_flick_cw_se(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.E, CardinalDirection.S) and is_moving_se(g)


def is_flick_cw_sw(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.S, CardinalDirection.W) and is_moving_sw(g)


def is_flick_cw_nw(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.W, CardinalDirection.N) and is_moving_nw(g)


# =========================================
# Flicks CCW
# =========================================


def is_flick_ccw_ne(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.E, CardinalDirection.N) and is_moving_ne(g)


def is_flick_ccw_se(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.S, CardinalDirection.E) and is_moving_se(g)


def is_flick_ccw_sw(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.W, CardinalDirection.S) and is_moving_sw(g)


def is_flick_ccw_nw(g: Gesture) -> bool:
    return _is_flick(g, CardinalDirection.N, CardinalDirection.W) and is_moving_nw(g)


# =========================================
# Utils
# =========================================


def _is_flick(g: Gesture, d1: CardinalDirection, d2: CardinalDirection) -> bool:
    g1, g2 = g.split(_SPLIT_POSITION)

    g1d1 = _get_cardinal_velocites(g1, d1)
    g1d2 = _get_cardinal_velocites(g1, d2)
    g2d1 = _get_cardinal_velocites(g2, d1)
    g2d2 = _get_cardinal_velocites(g2, d2)

    a = g1d1 > g2d1 * _FLICK_RATIO
    b = g2d2 > g1d2 * _FLICK_RATIO

    return a and b


def _get_cardinal_velocites(g: Gesture, direction: CardinalDirection) -> float:
    if direction is CardinalDirection.N:
        return g.total_velocity_n
    elif direction is CardinalDirection.E:
        return g.total_velocity_e
    elif direction is CardinalDirection.S:
        return g.total_velocity_s
    elif direction is CardinalDirection.W:
        return g.total_velocity_w

    raise ValueError(f"Flick not implemented for '{direction.name}'.")
