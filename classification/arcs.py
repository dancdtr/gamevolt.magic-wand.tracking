from classification.bounces import has_bounce_e2w, has_bounce_n2s, has_bounce_s2n, has_bounce_w2e
from classification.classifiers.inflections import (
    ends_with_x_turn_type_e2w,
    ends_with_x_turn_type_w2e,
    ends_with_y_turn_type_n2s,
    ends_with_y_turn_type_s2n,
)
from classification.directions import has_azimuth_e, has_azimuth_n, has_azimuth_s, has_azimuth_w
from classification.utils import _matches_curve
from detection.gesture import Gesture
from detection.turn_direction import TurnDirection
from gamevolt.maths.azimuth import Azimuth


# =========================================
# Curves 180 CW
# =========================================
def has_curve_180_cw_start_n(g: Gesture) -> bool:
    return ends_with_x_turn_type_e2w(g) and has_azimuth_s(g)


def has_curve_180_cw_start_e(g: Gesture) -> bool:
    return ends_with_y_turn_type_s2n(g) and has_azimuth_w(g)


def has_curve_180_cw_start_s(g: Gesture) -> bool:
    return ends_with_x_turn_type_w2e(g) and has_azimuth_n(g)


def has_curve_180_cw_start_w(g: Gesture) -> bool:
    a = ends_with_y_turn_type_n2s(g)
    b = has_azimuth_e(g)

    print(f"curve: {a} | {b}")

    return a and b


# =========================================
# Curves 180 CCW
# =========================================
def has_curve_180_ccw_start_n(g: Gesture) -> bool:
    return ends_with_x_turn_type_w2e(g) and has_azimuth_s(g)


def has_curve_180_ccw_start_e(g: Gesture) -> bool:
    return ends_with_y_turn_type_n2s(g) and has_azimuth_w(g)


def has_curve_180_ccw_start_s(g: Gesture) -> bool:
    return ends_with_x_turn_type_e2w(g) and has_azimuth_n(g)


def has_curve_180_ccw_start_w(g: Gesture) -> bool:
    return ends_with_y_turn_type_s2n(g) and has_azimuth_e(g)


# =========================================
# Arcs 180 CW
# =========================================
def is_arc_180_cw_start_n(g: Gesture) -> bool:
    return has_curve_180_cw_start_n(g) and has_bounce_e2w(g)


def is_arc_180_cw_start_e(g: Gesture) -> bool:
    return has_curve_180_cw_start_e(g) and has_bounce_s2n(g)


def is_arc_180_cw_start_s(g: Gesture) -> bool:
    return has_curve_180_cw_start_s(g) and has_bounce_w2e(g)


def is_arc_180_cw_start_w(g: Gesture) -> bool:
    return has_curve_180_cw_start_w(g) and has_bounce_n2s(g)


# =========================================
# Arcs 180 CCW
# =========================================
def is_arc_180_ccw_start_n(g: Gesture) -> bool:
    return has_curve_180_ccw_start_n(g) and has_bounce_w2e(g)


def is_arc_180_ccw_start_e(g: Gesture) -> bool:
    return has_curve_180_ccw_start_e(g) and has_bounce_n2s(g)


def is_arc_180_ccw_start_s(g: Gesture) -> bool:
    return has_curve_180_ccw_start_s(g) and has_bounce_e2w(g)


def is_arc_180_ccw_start_w(g: Gesture) -> bool:
    return has_curve_180_ccw_start_w(g) and has_bounce_s2n(g)


# =========================================
# Arcs 270 CW
# =========================================
def is_arc_270_cw_start_n(g: Gesture) -> bool:
    return _is_arc_270_cw(g, start=Azimuth.N)


def is_arc_270_cw_start_e(g: Gesture) -> bool:
    return _is_arc_270_cw(g, start=Azimuth.E)


def is_arc_270_cw_start_s(g: Gesture) -> bool:
    return _is_arc_270_cw(g, start=Azimuth.S)


def is_arc_270_cw_start_w(g: Gesture) -> bool:
    return _is_arc_270_cw(g, start=Azimuth.W)


# =========================================
# Arcs 270 CCW
# =========================================
def is_arc_270_ccw_start_n(g: Gesture) -> bool:
    return _is_arc_270_ccw(g, start=Azimuth.N)


def is_arc_270_ccw_start_e(g: Gesture) -> bool:
    return _is_arc_270_ccw(g, start=Azimuth.E)


def is_arc_270_ccw_start_s(g: Gesture) -> bool:
    return _is_arc_270_ccw(g, start=Azimuth.S)


def is_arc_270_ccw_start_w(g: Gesture) -> bool:
    return _is_arc_270_ccw(g, start=Azimuth.W)


# =========================================
# Arcs 360 CW
# =========================================
def is_arc_360_cw_start_n(g: Gesture) -> bool:
    return _is_arc_360_cw(g, start=Azimuth.N)


def is_arc_360_cw_start_e(g: Gesture) -> bool:
    return _is_arc_360_cw(g, start=Azimuth.E)


def is_arc_360_cw_start_s(g: Gesture) -> bool:
    return _is_arc_360_cw(g, start=Azimuth.S)


def is_arc_360_cw_start_w(g: Gesture) -> bool:
    return _is_arc_360_cw(g, start=Azimuth.W)


# =========================================
# Arcs 360 CCW
# =========================================
def is_arc_360_ccw_start_n(g: Gesture) -> bool:
    return _is_arc_360_ccw(g, start=Azimuth.N)


def is_arc_360_ccw_start_e(g: Gesture) -> bool:
    return _is_arc_360_ccw(g, start=Azimuth.E)


def is_arc_360_ccw_start_s(g: Gesture) -> bool:
    return _is_arc_360_ccw(g, start=Azimuth.S)


def is_arc_360_ccw_start_w(g: Gesture) -> bool:
    return _is_arc_360_ccw(g, start=Azimuth.W)


# =========================================
# Utils
# =========================================
def _is_arc_360_cw(g: Gesture, start: Azimuth) -> bool:
    return _is_arc_360(g, start, direction=TurnDirection.CW)


def _is_arc_360_ccw(g: Gesture, start: Azimuth) -> bool:
    return _is_arc_360(g, start, direction=TurnDirection.CCW)


def _is_arc_270_cw(g: Gesture, start: Azimuth) -> bool:
    return _is_arc_270(g, start, direction=TurnDirection.CW)


def _is_arc_270_ccw(g: Gesture, start: Azimuth) -> bool:
    return _is_arc_270(g, start, direction=TurnDirection.CCW)


def _is_arc_180_cw(g: Gesture, start: Azimuth) -> bool:
    return _is_arc_180(g, start, direction=TurnDirection.CW)


def _is_arc_180_ccw(g: Gesture, start: Azimuth) -> bool:
    return _is_arc_180(g, start, direction=TurnDirection.CCW)


def _is_arc_360(g: Gesture, start: Azimuth, direction: TurnDirection) -> bool:
    return _matches_curve(g=g, start=start, degrees=360, direction=direction, allow_tail_missing=1)


def _is_arc_270(g: Gesture, start: Azimuth, direction: TurnDirection) -> bool:
    return _matches_curve(g=g, start=start, degrees=270, direction=direction, allow_tail_missing=1)


def _is_arc_180(g: Gesture, start: Azimuth, direction: TurnDirection) -> bool:
    return _matches_curve(g=g, start=start, degrees=180, direction=direction, allow_tail_missing=1)
