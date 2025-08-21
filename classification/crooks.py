from classification.arcs import _matches_curve
from classification.directions import has_azimuth_e, has_azimuth_n, has_azimuth_s, has_azimuth_w
from detection.gesture import Gesture
from detection.turn_direction import TurnDirection
from gamevolt.maths.azimuth import Azimuth

_LINE_FUNCS = {
    Azimuth.N: has_azimuth_n,
    Azimuth.E: has_azimuth_e,
    Azimuth.S: has_azimuth_s,
    Azimuth.W: has_azimuth_w,
}

_SPLIT_POSITION = 0.25  # normalised time position of the gesture


# A crook is a straight line that transitions into a 270 deg arc (des)
# An inverse crook is a 270 deg arc that transitions into a straight line


# =========================================
# Crooks 270 CW
# =========================================
def is_crook_n_cw(g: Gesture) -> bool:
    return _is_crook_cw(g, line_start=Azimuth.N, arc_start=Azimuth.W)


def is_crook_e_cw(g: Gesture) -> bool:
    return _is_crook_cw(g, line_start=Azimuth.E, arc_start=Azimuth.N)


def is_crook_s_cw(g: Gesture) -> bool:
    return _is_crook_cw(g, line_start=Azimuth.S, arc_start=Azimuth.E)


def is_crook_w_cw(g: Gesture) -> bool:
    return _is_crook_cw(g, line_start=Azimuth.W, arc_start=Azimuth.S)


# =========================================
# Crooks 270 CCW
# =========================================
def is_crook_n_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.N, arc_start=Azimuth.E)


def is_crook_e_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.E, arc_start=Azimuth.N)


def is_crook_s_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.S, arc_start=Azimuth.W)


def is_crook_w_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.W, arc_start=Azimuth.S)


# =========================================
# Inverse Crooks 270 CW
# =========================================
def is_inverse_crook_n_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, line_start=Azimuth.N, arc_start=Azimuth.W)


def is_inverse_crook_e_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, line_start=Azimuth.E, arc_start=Azimuth.N)


def is_inverse_crook_s_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, line_start=Azimuth.S, arc_start=Azimuth.E)


def is_inverse_crook_w_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, line_start=Azimuth.W, arc_start=Azimuth.S)


# =========================================
# Inverse Crooks 270 CCW
# =========================================
def is_inverse_crook_n_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, line_start=Azimuth.N, arc_start=Azimuth.E)


def is_inverse_crook_e_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, line_start=Azimuth.E, arc_start=Azimuth.N)


def is_inverse_crook_s_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, line_start=Azimuth.S, arc_start=Azimuth.W)


def is_inverse_crook_w_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, line_start=Azimuth.W, arc_start=Azimuth.S)


# =========================================
# Utils
# =========================================
def _is_crook_cw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_crook(g, line_start, arc_start, TurnDirection.CW)


def _is_crook_ccw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_crook(g, line_start, arc_start, TurnDirection.CCW)


def _is_crook(g: Gesture, line_start: Azimuth, arc_start: Azimuth, direction: TurnDirection) -> bool:
    return _is_line_and_arc_270_compound(g, line_start, arc_start, direction, arc_first=False)


def _is_inverse_crook_cw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_inverse_crook(g, line_start, arc_start, TurnDirection.CW)


def _is_inverse_crook_ccw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_inverse_crook(g, line_start, arc_start, TurnDirection.CCW)


def _is_inverse_crook(g: Gesture, line_start: Azimuth, arc_start: Azimuth, direction: TurnDirection) -> bool:
    return _is_line_and_arc_270_compound(g, line_start, arc_start, direction, arc_first=True)


def _is_line_and_arc_270_compound(g: Gesture, line_start: Azimuth, arc_start: Azimuth, direction: TurnDirection, arc_first: bool) -> bool:
    g1, g2 = g.split(_SPLIT_POSITION)
    if arc_first:
        g1, g2 = g2, g1

    return _LINE_FUNCS[line_start](g1) and _matches_curve(
        g=g2,
        start=arc_start,
        degrees=270,
        direction=direction,
        allow_head_missing=1,
        allow_tail_missing=1,
    )
