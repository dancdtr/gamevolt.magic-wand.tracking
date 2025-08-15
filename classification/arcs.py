from classification.curves import (
    is_curve_ccw_start_e,
    is_curve_ccw_start_n,
    is_curve_ccw_start_s,
    is_curve_ccw_start_w,
    is_curve_cw_start_e,
    is_curve_cw_start_n,
    is_curve_cw_start_s,
    is_curve_cw_start_w,
)
from classification.directions import is_direction_e, is_direction_n, is_direction_s, is_direction_w
from classification.velocities import is_velocity_e, is_velocity_n, is_velocity_s, is_velocity_w
from detection.gesture import Gesture


# =========================================
# Semi CW Arcs
# =========================================
def is_arc_half_cw_start_n(g: Gesture) -> bool:
    return is_velocity_s(g) and is_direction_s(g.direction) and is_curve_cw_start_n(g)


def is_arc_half_cw_start_e(g: Gesture) -> bool:
    return is_velocity_w(g) and is_direction_w(g.direction) and is_curve_cw_start_e(g)


def is_arc_half_cw_start_s(g: Gesture) -> bool:
    return is_velocity_n(g) and is_direction_n(g.direction) and is_curve_cw_start_s(g)


def is_arc_half_cw_start_w(g: Gesture) -> bool:
    return is_velocity_e(g) and is_direction_e(g.direction) and is_curve_cw_start_w(g)


# =========================================
# Semi CCW Arcs
# =========================================
def is_arc_half_ccw_start_n(g: Gesture) -> bool:
    return is_velocity_s(g) and is_direction_s(g.direction) and is_curve_ccw_start_n(g)


def is_arc_half_ccw_start_e(g: Gesture) -> bool:
    return is_velocity_w(g) and is_direction_w(g.direction) and is_curve_ccw_start_e(g)


def is_arc_half_ccw_start_s(g: Gesture) -> bool:
    return is_velocity_n(g) and is_direction_n(g.direction) and is_curve_ccw_start_s(g)


def is_arc_half_ccw_start_w(g: Gesture) -> bool:
    return is_velocity_e(g) and is_direction_e(g.direction) and is_curve_ccw_start_w(g)
