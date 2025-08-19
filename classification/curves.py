from classification.bounces import has_bounce_e2w, has_bounce_n2s, has_bounce_s2n, has_bounce_w2e
from classification.classifiers.inflections import (
    ends_with_x_turn_type_e2w,
    ends_with_x_turn_type_w2e,
    ends_with_y_turn_type_n2s,
    ends_with_y_turn_type_s2n,
)
from classification.utils import matches_curve
from detection.gesture import Gesture
from detection.turn import TurnType


# =========================================
# Curves 180 CW
# =========================================
def is_curve_180_cw_start_n(g: Gesture) -> bool:
    return ends_with_x_turn_type_e2w(g) and has_bounce_e2w(g)


def is_curve_180_cw_start_e(g: Gesture) -> bool:
    return ends_with_y_turn_type_s2n(g) and has_bounce_s2n(g)


def is_curve_180_cw_start_s(g: Gesture) -> bool:
    return ends_with_x_turn_type_w2e(g) and has_bounce_w2e(g)


def is_curve_180_cw_start_w(g: Gesture) -> bool:
    return ends_with_y_turn_type_n2s(g) and has_bounce_n2s(g)


# =========================================
# Curves 180 CCW
# =========================================
def is_curve_180_ccw_start_n(g: Gesture) -> bool:
    return ends_with_x_turn_type_w2e(g) and has_bounce_w2e(g)


def is_curve_180_ccw_start_e(g: Gesture) -> bool:
    return ends_with_y_turn_type_n2s(g) and has_bounce_n2s(g)


def is_curve_180_ccw_start_s(g: Gesture) -> bool:
    return ends_with_x_turn_type_e2w(g) and has_bounce_e2w(g)


def is_curve_180_ccw_start_w(g: Gesture) -> bool:
    return ends_with_y_turn_type_s2n(g) and has_bounce_s2n(g)


# =========================================
# Curves 270 CW
# =========================================
def is_curve_270_cw_start_n(g: Gesture) -> bool:
    return matches_curve(g, TurnType.E2W, TurnType.S2N, TurnType.W2E)


def is_curve_270_cw_start_e(g: Gesture) -> bool:
    return matches_curve(g, TurnType.S2N, TurnType.W2E, TurnType.N2S)


def is_curve_270_cw_start_s(g: Gesture) -> bool:
    return matches_curve(g, TurnType.W2E, TurnType.N2S, TurnType.E2W)


def is_curve_270_cw_start_w(g: Gesture) -> bool:
    return matches_curve(g, TurnType.N2S, TurnType.E2W, TurnType.S2N)


# =========================================
# Curves 270 CCW
# =========================================
def is_curve_270_ccw_start_n(g: Gesture) -> bool:
    return matches_curve(g, TurnType.W2E, TurnType.S2N, TurnType.E2W)


def is_curve_270_ccw_start_e(g: Gesture) -> bool:
    return matches_curve(g, TurnType.N2S, TurnType.W2E, TurnType.S2N)


def is_curve_270_ccw_start_s(g: Gesture) -> bool:
    return matches_curve(g, TurnType.E2W, TurnType.N2S, TurnType.W2E)


def is_curve_270_ccw_start_w(g: Gesture) -> bool:
    return matches_curve(g, TurnType.S2N, TurnType.E2W, TurnType.N2S)


# =========================================
# Curves 360 CW
# =========================================
def is_curve_360_cw_start_n(g: Gesture) -> bool:
    return matches_curve(g, TurnType.E2W, TurnType.S2N, TurnType.W2E, TurnType.N2S)


def is_curve_360_cw_start_e(g: Gesture) -> bool:
    return matches_curve(g, TurnType.S2N, TurnType.W2E, TurnType.N2S, TurnType.E2W)


def is_curve_360_cw_start_s(g: Gesture) -> bool:
    return matches_curve(g, TurnType.W2E, TurnType.N2S, TurnType.E2W, TurnType.S2N)


def is_curve_360_cw_start_w(g: Gesture) -> bool:
    return matches_curve(g, TurnType.N2S, TurnType.E2W, TurnType.S2N, TurnType.W2E)


# =========================================
# Curves 360 CCW
# =========================================
def is_curve_360_ccw_start_n(g: Gesture) -> bool:
    return matches_curve(g, TurnType.W2E, TurnType.S2N, TurnType.E2W, TurnType.N2S)


def is_curve_360_ccw_start_e(g: Gesture) -> bool:
    return matches_curve(g, TurnType.N2S, TurnType.W2E, TurnType.S2N, TurnType.E2W)


def is_curve_360_ccw_start_s(g: Gesture) -> bool:
    return matches_curve(g, TurnType.E2W, TurnType.N2S, TurnType.W2E, TurnType.S2N)


def is_curve_360_ccw_start_w(g: Gesture) -> bool:
    return matches_curve(g, TurnType.S2N, TurnType.E2W, TurnType.N2S, TurnType.W2E)
