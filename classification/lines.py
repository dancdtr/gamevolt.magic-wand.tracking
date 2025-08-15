from classification.directions import (
    is_direction_e,
    is_direction_ene,
    is_direction_ese,
    is_direction_n,
    is_direction_ne,
    is_direction_nne,
    is_direction_nnw,
    is_direction_nw,
    is_direction_s,
    is_direction_se,
    is_direction_sse,
    is_direction_ssw,
    is_direction_sw,
    is_direction_w,
    is_direction_wnw,
    is_direction_wsw,
)
from classification.velocities import (
    is_velocity_e,
    is_velocity_ene,
    is_velocity_ese,
    is_velocity_n,
    is_velocity_ne,
    is_velocity_nne,
    is_velocity_nnw,
    is_velocity_nw,
    is_velocity_s,
    is_velocity_se,
    is_velocity_sse,
    is_velocity_ssw,
    is_velocity_sw,
    is_velocity_w,
    is_velocity_wnw,
    is_velocity_wsw,
)
from detection.gesture import Gesture


# =========================================
# Cardinal lines
# =========================================
def is_line_n(g: Gesture) -> bool:
    return is_velocity_n(g) and is_direction_n(g.direction)


def is_line_e(g: Gesture) -> bool:
    return is_velocity_e(g) and is_direction_e(g.direction)


def is_line_s(g: Gesture) -> bool:
    return is_velocity_s(g) and is_direction_s(g.direction)


def is_line_w(g: Gesture) -> bool:
    return is_velocity_w(g) and is_direction_w(g.direction)


# =========================================
# Intercardinal lines
# =========================================
def is_line_ne(g: Gesture) -> bool:
    return is_velocity_ne(g) and is_direction_ne(g.direction)


def is_line_se(g: Gesture) -> bool:
    return is_velocity_se(g) and is_direction_se(g.direction)


def is_line_sw(g: Gesture) -> bool:
    return is_velocity_sw(g) and is_direction_sw(g.direction)


def is_line_nw(g: Gesture) -> bool:
    return is_velocity_nw(g) and is_direction_nw(g.direction)


# =========================================
# Secondary Intercardinal lines
# =========================================
def is_line_nne(g: Gesture) -> bool:
    return is_velocity_nne(g) and is_direction_nne(g.direction)


def is_line_ene(g: Gesture) -> bool:
    return is_velocity_ene(g) and is_direction_ene(g.direction)


def is_line_ese(g: Gesture) -> bool:
    return is_velocity_ese(g) and is_direction_ese(g.direction)


def is_line_sse(g: Gesture) -> bool:
    return is_velocity_sse(g) and is_direction_sse(g.direction)


def is_line_ssw(g: Gesture) -> bool:
    return is_velocity_ssw(g) and is_direction_ssw(g.direction)


def is_line_wsw(g: Gesture) -> bool:
    return is_velocity_wsw(g) and is_direction_wsw(g.direction)


def is_line_wnw(g: Gesture) -> bool:
    return is_velocity_wnw(g) and is_direction_wnw(g.direction)


def is_line_nnw(g: Gesture) -> bool:
    return is_velocity_nnw(g) and is_direction_nnw(g.direction)
