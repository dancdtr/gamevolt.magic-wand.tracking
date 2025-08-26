from classification.arcs import (
    has_curve_180_ccw_start_e,
    has_curve_180_ccw_start_n,
    has_curve_180_ccw_start_s,
    has_curve_180_ccw_start_w,
    has_curve_180_cw_start_e,
    has_curve_180_cw_start_n,
    has_curve_180_cw_start_s,
    has_curve_180_cw_start_w,
)
from classification.lines import is_line_e, is_line_n, is_line_s, is_line_w
from classification.utils import is_line_and_arc_compound
from detection.gesture import Gesture
from detection.turn_direction import TurnDirection
from gamevolt.maths.azimuth import Azimuth

_HOOK_SPLIT_TIME = 0.65  # normalised time position of the gesture
_INVERSE_HOOK_SPLIT_TIME = 1 - _HOOK_SPLIT_TIME

# A cardinal hook is a straight line that transitions into a 180 deg arc (des)
# An inverse cardinal hook is a 180 deg arc that transitions into a straight line
_MIN_LINE_DURATION = 0.15
_MAX_LINE_DURATION = 0.6
_MIN_ARC_DURATION = 0.25
_MAX_ARC_DURATION = 1

_LINE_FUNCS = {
    Azimuth.N: is_line_n,
    Azimuth.E: is_line_e,
    Azimuth.S: is_line_s,
    Azimuth.W: is_line_w,
}

_CURVE_CW_START_POSITION_FUNCS = {
    Azimuth.N: has_curve_180_cw_start_n,
    Azimuth.E: has_curve_180_cw_start_e,
    Azimuth.S: has_curve_180_cw_start_s,
    Azimuth.W: has_curve_180_cw_start_w,
}

_CURVE_CCW_START_POSITION_FUNCS = {
    Azimuth.N: has_curve_180_ccw_start_n,
    Azimuth.E: has_curve_180_ccw_start_e,
    Azimuth.S: has_curve_180_ccw_start_s,
    Azimuth.W: has_curve_180_ccw_start_w,
}


# =========================================
# Cardinal Hooks CW
# =========================================
def is_hook_n_cw(g: Gesture) -> bool:
    return _is_hook_cw(g, line_direction=Azimuth.N, curve_start=Azimuth.W)


def is_hook_e_cw(g: Gesture) -> bool:
    return _is_hook_cw(g, line_direction=Azimuth.E, curve_start=Azimuth.N)


def is_hook_s_cw(g: Gesture) -> bool:
    return _is_hook_cw(g, line_direction=Azimuth.S, curve_start=Azimuth.E)


def is_hook_w_cw(g: Gesture) -> bool:
    return _is_hook_cw(g, line_direction=Azimuth.W, curve_start=Azimuth.S)


# =========================================
# Cardinal Hooks CCW
# =========================================
def is_hook_n_ccw(g: Gesture) -> bool:
    return _is_hook_ccw(g, line_direction=Azimuth.N, curve_start=Azimuth.E)


def is_hook_e_ccw(g: Gesture) -> bool:
    return _is_hook_ccw(g, line_direction=Azimuth.E, curve_start=Azimuth.S)


def is_hook_s_ccw(g: Gesture) -> bool:
    return _is_hook_ccw(g, line_direction=Azimuth.S, curve_start=Azimuth.W)


def is_hook_w_ccw(g: Gesture) -> bool:
    return _is_hook_ccw(g, line_direction=Azimuth.W, curve_start=Azimuth.N)


# =========================================
# Inverse Cardinal Hooks CW
# =========================================
def is_inverse_hook_n_cw(g: Gesture) -> bool:
    return _is_inverse_hook_cw(g, curve_start=Azimuth.W, line_direction=Azimuth.S)


def is_inverse_hook_e_cw(g: Gesture) -> bool:
    return _is_inverse_hook_cw(g, curve_start=Azimuth.S, line_direction=Azimuth.W)


def is_inverse_hook_s_cw(g: Gesture) -> bool:
    return _is_inverse_hook_cw(g, curve_start=Azimuth.W, line_direction=Azimuth.N)


def is_inverse_hook_w_cw(g: Gesture) -> bool:
    return _is_inverse_hook_cw(g, curve_start=Azimuth.N, line_direction=Azimuth.E)


# =========================================
# Inverse Cardinal Hooks CCW
# =========================================
def is_inverse_hook_n_ccw(g: Gesture) -> bool:
    return _is_inverse_hook_ccw(g, curve_start=Azimuth.S, line_direction=Azimuth.S)


def is_inverse_hook_e_ccw(g: Gesture) -> bool:
    return _is_inverse_hook_ccw(g, curve_start=Azimuth.W, line_direction=Azimuth.W)


def is_inverse_hook_s_ccw(g: Gesture) -> bool:
    return _is_inverse_hook_ccw(g, curve_start=Azimuth.N, line_direction=Azimuth.N)


def is_inverse_hook_w_ccw(g: Gesture) -> bool:
    return _is_inverse_hook_ccw(g, curve_start=Azimuth.E, line_direction=Azimuth.E)


# =========================================
# Utils
# =========================================
def _is_hook_cw(g: Gesture, line_direction: Azimuth, curve_start: Azimuth) -> bool:
    return _is_hook(g=g, line_direction=line_direction, curve_start=curve_start, direction=TurnDirection.CW)


def _is_hook_ccw(g: Gesture, line_direction: Azimuth, curve_start: Azimuth) -> bool:
    return _is_hook(g=g, line_direction=line_direction, curve_start=curve_start, direction=TurnDirection.CCW)


def _is_inverse_hook_cw(g: Gesture, curve_start: Azimuth, line_direction: Azimuth) -> bool:
    return _is_inverse_hook(g=g, line_direction=line_direction, curve_start=curve_start, direction=TurnDirection.CW)


def _is_inverse_hook_ccw(g: Gesture, curve_start: Azimuth, line_direction: Azimuth) -> bool:
    return _is_inverse_hook(g=g, line_direction=line_direction, curve_start=curve_start, direction=TurnDirection.CCW)


def _is_hook(g: Gesture, line_direction: Azimuth, curve_start: Azimuth, direction: TurnDirection) -> bool:
    g_line, g_curve = g.split(_HOOK_SPLIT_TIME)

    if _MIN_LINE_DURATION > g_line.duration or g_line.duration > _MAX_LINE_DURATION:
        print(f"Failed line: {g_line.duration}")
        return False

    if _MIN_ARC_DURATION > g_curve.duration or g_curve.duration > _MAX_ARC_DURATION:
        print(f"Failed arc: {g_curve.duration}")
        return False

    line_func = _LINE_FUNCS[line_direction]
    curve_func = (
        _CURVE_CW_START_POSITION_FUNCS[curve_start] if direction is TurnDirection.CW else _CURVE_CCW_START_POSITION_FUNCS[curve_start]
    )
    a = line_func(g_line)
    b = curve_func(g_curve)

    print(a, b)
    return a and b


def _is_inverse_hook(g: Gesture, curve_start: Azimuth, line_direction: Azimuth, direction: TurnDirection) -> bool:
    return _is_line_and_arc_180_compound(
        g=g,
        line_start=line_direction,
        arc_start=curve_start,
        direction=direction,
        arc_first=True,
        split_time=_INVERSE_HOOK_SPLIT_TIME,
    )
