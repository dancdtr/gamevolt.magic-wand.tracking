from classification.bounces import has_bounce_e2w, has_bounce_n2s, has_bounce_s2n, has_bounce_w2e
from classification.classifiers.inflections import (
    ends_with_x_turn_type_e2w,
    ends_with_x_turn_type_w2e,
    ends_with_y_turn_type_n2s,
    ends_with_y_turn_type_s2n,
    starts_with_x_turn_type_e2w,
    starts_with_x_turn_type_w2e,
    starts_with_y_turn_type_n2s,
    starts_with_y_turn_type_s2n,
)
from detection.gesture import Gesture


# =========================================
# Semi CW Curves
# =========================================
def is_curve_cw_start_n(g: Gesture) -> bool:
    return starts_with_x_turn_type_e2w(g) and has_bounce_e2w(g)


def is_curve_cw_start_e(g: Gesture) -> bool:
    return starts_with_y_turn_type_s2n(g) and has_bounce_s2n(g)


def is_curve_cw_start_s(g: Gesture) -> bool:
    return starts_with_x_turn_type_w2e(g) and has_bounce_w2e(g)


def is_curve_cw_start_w(g: Gesture) -> bool:
    return starts_with_y_turn_type_n2s(g) and has_bounce_n2s(g)


# =========================================
# Semi CCW Curves
# =========================================
def is_curve_ccw_start_n(g: Gesture) -> bool:
    return ends_with_x_turn_type_w2e(g) and has_bounce_w2e(g)


def is_curve_ccw_start_e(g: Gesture) -> bool:
    return ends_with_y_turn_type_n2s(g) and has_bounce_n2s(g)


def is_curve_ccw_start_s(g: Gesture) -> bool:
    return ends_with_x_turn_type_e2w(g) and has_bounce_e2w(g)


def is_curve_ccw_start_w(g: Gesture) -> bool:
    return ends_with_y_turn_type_s2n(g) and has_bounce_s2n(g)
