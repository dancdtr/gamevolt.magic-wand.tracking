from classification.utils import is_line_and_arc_270_compound
from gamevolt.maths.azimuth import Azimuth
from gestures.gesture import Gesture
from gestures.turn_direction import TurnDirection

_CROOK_SPLIT_TIME = 0.25  # normalised time position of the gesture
_INVERSE_CROOK_SPLIT_TIME = 1 - _CROOK_SPLIT_TIME


# A crook is a straight line that transitions into a 270 deg arc (des)
# An inverse crook is a 270 deg arc that transitions into a straight line


# =========================================
# Cardinal Crooks 270 CW
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
# Cardinal Crooks 270 CCW
# =========================================
def is_crook_n_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.N, arc_start=Azimuth.E)


def is_crook_e_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.E, arc_start=Azimuth.S)


def is_crook_s_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.S, arc_start=Azimuth.W)


def is_crook_w_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.W, arc_start=Azimuth.N)


# =========================================
# Inverse Cardinal Crooks 270 CW
# =========================================
def is_inverse_crook_s_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.S, line_start=Azimuth.S)


def is_inverse_crook_w_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.W, line_start=Azimuth.W)


def is_inverse_crook_n_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.N, line_start=Azimuth.N)


def is_inverse_crook_e_cw(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.E, line_start=Azimuth.E)


# =========================================
# Inverse Cardinal Crooks 270 CCW
# =========================================
def is_inverse_crook_s_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.S, line_start=Azimuth.S)


def is_inverse_crook_w_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.W, line_start=Azimuth.W)


def is_inverse_crook_n_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.N, line_start=Azimuth.N)


def is_inverse_crook_e_ccw(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.E, line_start=Azimuth.E)


# =========================================
# Utils
# =========================================
def _is_crook_cw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_crook(g, line_start, arc_start, TurnDirection.CW)


def _is_crook_ccw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_crook(g, line_start, arc_start, TurnDirection.CCW)


def _is_inverse_crook_cw(g: Gesture, arc_start: Azimuth, line_start: Azimuth) -> bool:
    return _is_inverse_crook(g, line_start, arc_start, TurnDirection.CW)


def _is_inverse_crook_ccw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_inverse_crook(g, line_start, arc_start, TurnDirection.CCW)


def _is_crook(g: Gesture, line_start: Azimuth, arc_start: Azimuth, direction: TurnDirection) -> bool:
    return is_line_and_arc_270_compound(
        g=g,
        line_start=line_start,
        arc_start=arc_start,
        direction=direction,
        arc_first=False,
        split_time=_CROOK_SPLIT_TIME,
    )


def _is_inverse_crook(g: Gesture, arc_start: Azimuth, line_start: Azimuth, direction: TurnDirection) -> bool:
    return is_line_and_arc_270_compound(
        g=g,
        line_start=line_start,
        arc_start=arc_start,
        direction=direction,
        arc_first=True,
        split_time=_INVERSE_CROOK_SPLIT_TIME,
    )
