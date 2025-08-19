from classification.directions import (
    has_azimuth_e,
    has_azimuth_n,
    has_azimuth_ne,
    has_azimuth_nw,
    has_azimuth_s,
    has_azimuth_se,
    has_azimuth_sw,
    has_azimuth_w,
    is_direction_ene,
    is_direction_ese,
    is_direction_nne,
    is_direction_nnw,
    is_direction_sse,
    is_direction_ssw,
    is_direction_wnw,
    is_direction_wsw,
)
from classification.velocities import (
    has_velocity_e,
    has_velocity_n,
    has_velocity_ne,
    has_velocity_nw,
    has_velocity_s,
    has_velocity_se,
    has_velocity_sw,
    has_velocity_w,
    is_velocity_ene,
    is_velocity_ese,
    is_velocity_nne,
    is_velocity_nnw,
    is_velocity_sse,
    is_velocity_ssw,
    is_velocity_wnw,
    is_velocity_wsw,
)
from detection.gesture import Gesture


# =========================================
# Cardinal lines
# =========================================
def is_line_n(g: Gesture) -> bool:
    return has_velocity_n(g) and has_azimuth_n(g.azimuth)


def is_line_e(g: Gesture) -> bool:
    return has_velocity_e(g) and has_azimuth_e(g.azimuth)


def is_line_s(g: Gesture) -> bool:
    return has_velocity_s(g) and has_azimuth_s(g.azimuth)


def is_line_w(g: Gesture) -> bool:
    return has_velocity_w(g) and has_azimuth_w(g.azimuth)


# =========================================
# Intercardinal lines
# =========================================
def is_line_ne(g: Gesture) -> bool:
    return has_velocity_ne(g) and has_azimuth_ne(g.azimuth)


def is_line_se(g: Gesture) -> bool:
    return has_velocity_se(g) and has_azimuth_se(g.azimuth)


def is_line_sw(g: Gesture) -> bool:
    return has_velocity_sw(g) and has_azimuth_sw(g.azimuth)


def is_line_nw(g: Gesture) -> bool:
    return has_velocity_nw(g) and has_azimuth_nw(g.azimuth)


# =========================================
# Sub Intercardinal lines
# =========================================
def is_line_nne(g: Gesture) -> bool:
    return is_velocity_nne(g) and is_direction_nne(g.azimuth)


def is_line_ene(g: Gesture) -> bool:
    return is_velocity_ene(g) and is_direction_ene(g.azimuth)


def is_line_ese(g: Gesture) -> bool:
    return is_velocity_ese(g) and is_direction_ese(g.azimuth)


def is_line_sse(g: Gesture) -> bool:
    return is_velocity_sse(g) and is_direction_sse(g.azimuth)


def is_line_ssw(g: Gesture) -> bool:
    return is_velocity_ssw(g) and is_direction_ssw(g.azimuth)


def is_line_wsw(g: Gesture) -> bool:
    return is_velocity_wsw(g) and is_direction_wsw(g.azimuth)


def is_line_wnw(g: Gesture) -> bool:
    return is_velocity_wnw(g) and is_direction_wnw(g.azimuth)


def is_line_nnw(g: Gesture) -> bool:
    return is_velocity_nnw(g) and is_direction_nnw(g.azimuth)
