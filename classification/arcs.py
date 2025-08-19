from classification.curves import (
    is_curve_180_ccw_start_e,
    is_curve_180_ccw_start_n,
    is_curve_180_ccw_start_s,
    is_curve_180_ccw_start_w,
    is_curve_180_cw_start_e,
    is_curve_180_cw_start_n,
    is_curve_180_cw_start_s,
    is_curve_180_cw_start_w,
)
from classification.velocities import has_velocity_e, has_velocity_n, has_velocity_s, has_velocity_w
from detection.gesture import Gesture


# =========================================
# Arcs 180 CW
# =========================================
def is_arc_180_cw_start_n(g: Gesture) -> bool:
    return has_velocity_s(g) and is_curve_180_cw_start_n(g)


def is_arc_180_cw_start_e(g: Gesture) -> bool:
    return has_velocity_w(g) and is_curve_180_cw_start_e(g)


def is_arc_180_cw_start_s(g: Gesture) -> bool:
    return has_velocity_n(g) and is_curve_180_cw_start_s(g)


def is_arc_180_cw_start_w(g: Gesture) -> bool:
    return has_velocity_e(g) and is_curve_180_cw_start_w(g)


# =========================================
# Arcs 180 CCW
# =========================================
def is_arc_180_ccw_start_n(g: Gesture) -> bool:
    return has_velocity_s(g) and is_curve_180_ccw_start_n(g)


def is_arc_180_ccw_start_e(g: Gesture) -> bool:
    return has_velocity_w(g) and is_curve_180_ccw_start_e(g)


def is_arc_180_ccw_start_s(g: Gesture) -> bool:
    return has_velocity_n(g) and is_curve_180_ccw_start_s(g)


def is_arc_180_ccw_start_w(g: Gesture) -> bool:
    return has_velocity_e(g) and is_curve_180_ccw_start_w(g)
