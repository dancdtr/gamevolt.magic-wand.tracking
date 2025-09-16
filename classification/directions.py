from enum import Enum, auto

from classification.lines import has_azimuth_in_range
from detection.gesture import Gesture
from gamevolt.maths.azimuth import Azimuth


class Direction(Enum):
    NONE = auto()
    NORTHWARD = auto()
    EASTWARD = auto()
    SOUTHWARD = auto()
    WESTWARD = auto()


_CARDINAL_ANGLE_VARIANCE = 22.5
_MOVING_RATIO = 3


# =========================================
# Cardinal Directions
# =========================================


def has_azimuth_n(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.N, _CARDINAL_ANGLE_VARIANCE)


def has_azimuth_e(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.E, _CARDINAL_ANGLE_VARIANCE)


def has_azimuth_s(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.S, _CARDINAL_ANGLE_VARIANCE)


def has_azimuth_w(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.W, _CARDINAL_ANGLE_VARIANCE)


# =========================================
# General Movements
# =========================================


def get_horizontal_direction(g: Gesture) -> Direction:
    if is_moving_e(g):
        return Direction.EASTWARD
    elif is_moving_w(g):
        return Direction.WESTWARD
    return Direction.NONE


def get_vertical_dir(g: Gesture) -> Direction:
    if is_moving_n(g):
        return Direction.NORTHWARD
    elif is_moving_s(g):
        return Direction.SOUTHWARD

    return Direction.NONE


def is_moving_n(g: Gesture) -> bool:
    return g.total_neg_y > g.total_pos_y * _MOVING_RATIO


def is_moving_e(g: Gesture) -> bool:
    return g.total_neg_x > g.total_pos_x * _MOVING_RATIO


def is_moving_s(g: Gesture) -> bool:
    return g.total_pos_y > g.total_neg_y * _MOVING_RATIO


def is_moving_w(g: Gesture) -> bool:
    return g.total_pos_x > g.total_neg_x * _MOVING_RATIO


def is_moving_e2w(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.E, _CARDINAL_ANGLE_VARIANCE)


# =========================================
# Utils
# =========================================
