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

_SPLIT_TIME = 0.25  # normalised time position of the gesture
_MIN_LINE_DURATION = 0.15
_MAX_LINE_DURATION = 0.6
_MIN_ARC_DURATION = 0.25
_MAX_ARC_DURATION = 1
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
    return _is_crook_ccw(g, line_start=Azimuth.E, arc_start=Azimuth.S)


def is_crook_s_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.S, arc_start=Azimuth.W)


def is_crook_w_ccw(g: Gesture) -> bool:
    return _is_crook_ccw(g, line_start=Azimuth.W, arc_start=Azimuth.N)


# =========================================
# Inverse Crooks 270 CW
# =========================================
def is_inverse_crook_cw_s(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.S, line_start=Azimuth.S)


def is_inverse_crook_cw_w(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.W, line_start=Azimuth.W)


def is_inverse_crook_cw_n(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.N, line_start=Azimuth.N)


def is_inverse_crook_cw_e(g: Gesture) -> bool:
    return _is_inverse_crook_cw(g, arc_start=Azimuth.E, line_start=Azimuth.E)


# =========================================
# Inverse Crooks 270 CCW
# =========================================
def is_inverse_crook_ccw_s(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.S, line_start=Azimuth.S)


def is_inverse_crook_ccw_w(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.W, line_start=Azimuth.W)


def is_inverse_crook_ccw_n(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.N, line_start=Azimuth.N)


def is_inverse_crook_ccw_e(g: Gesture) -> bool:
    return _is_inverse_crook_ccw(g, arc_start=Azimuth.E, line_start=Azimuth.E)


# =========================================
# Utils
# =========================================
def _is_crook_cw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_crook(g, line_start, arc_start, TurnDirection.CW)


def _is_crook_ccw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_crook(g, line_start, arc_start, TurnDirection.CCW)


def _is_crook(g: Gesture, line_start: Azimuth, arc_start: Azimuth, direction: TurnDirection) -> bool:
    return _is_line_and_arc_270_compound(g, line_start, arc_start, direction, arc_first=False)


def _is_inverse_crook_cw(g: Gesture, arc_start: Azimuth, line_start: Azimuth) -> bool:
    return _is_inverse_crook(g, line_start, arc_start, TurnDirection.CW)


def _is_inverse_crook_ccw(g: Gesture, line_start: Azimuth, arc_start: Azimuth) -> bool:
    return _is_inverse_crook(g, line_start, arc_start, TurnDirection.CCW)


def _is_inverse_crook(g: Gesture, arc_start: Azimuth, line_start: Azimuth, direction: TurnDirection) -> bool:
    return _is_line_and_arc_270_compound(g=g, line_start=line_start, arc_start=arc_start, direction=direction, arc_first=True)


def _is_line_and_arc_270_compound(g: Gesture, line_start: Azimuth, arc_start: Azimuth, direction: TurnDirection, arc_first: bool) -> bool:
    split_time = 1 - _SPLIT_TIME if arc_first else _SPLIT_TIME

    g_line, g_arc = g.split(split_time)
    if arc_first:
        g_line, g_arc = g_arc, g_line

    if _MIN_LINE_DURATION > g_line.duration or g_line.duration > _MAX_LINE_DURATION:
        print(f"Failed line: {g_line.duration}")
        return False

    if _MIN_ARC_DURATION > g_arc.duration or g_arc.duration > _MAX_ARC_DURATION:
        print(f"Failed arc: {g_arc.duration}")
        return False

    return _LINE_FUNCS[line_start](g_line) and _matches_curve(
        g=g_arc,
        start=arc_start,
        degrees=270,
        direction=direction,
        allow_head_missing=1,
        allow_tail_missing=1,
    )
