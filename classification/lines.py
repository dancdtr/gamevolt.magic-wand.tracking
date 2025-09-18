from gamevolt.iterables.iter_tools import equals_single
from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.extremum import Extremum
from gestures.gesture import Gesture

_CARDINAL_ANGLE_VARIANCE = 22.5
_INTERCARDINAL_ANGLE_VARIANCE = 22.5
_SUBINTERCARDINAL_ANGLE_VARIANCE = 22.5

_MIN_VELOCITY = 60

_SPLIT_SUBCARDINALS = {
    Azimuth.NE: (Azimuth.N, Azimuth.E),
    Azimuth.SE: (Azimuth.S, Azimuth.E),
    Azimuth.SW: (Azimuth.S, Azimuth.W),
    Azimuth.NW: (Azimuth.N, Azimuth.W),
}

_SPLIT_SUBINTERCARDINALS = {
    Azimuth.NNE: (Azimuth.N, Azimuth.NE),
    Azimuth.ENE: (Azimuth.E, Azimuth.NE),
    Azimuth.ESE: (Azimuth.E, Azimuth.SE),
    Azimuth.SSE: (Azimuth.S, Azimuth.SE),
    Azimuth.SSW: (Azimuth.S, Azimuth.SW),
    Azimuth.WSW: (Azimuth.W, Azimuth.SW),
    Azimuth.WNW: (Azimuth.W, Azimuth.NW),
    Azimuth.NNW: (Azimuth.N, Azimuth.NW),
}


# =========================================
# Cardinal lines
# =========================================
def is_line_n(g: Gesture) -> bool:
    return _is_line_cardinal(g, Azimuth.N)


def is_line_e(g: Gesture) -> bool:
    return _is_line_cardinal(g, Azimuth.E)


def is_line_s(g: Gesture) -> bool:
    return _is_line_cardinal(g, Azimuth.S)


def is_line_w(g: Gesture) -> bool:
    return _is_line_cardinal(g, Azimuth.W)


# =========================================
# Intercardinal lines
# =========================================
def is_line_ne(g: Gesture) -> bool:
    return _is_line_intercardinal(g, Azimuth.NE)


def is_line_se(g: Gesture) -> bool:
    return _is_line_intercardinal(g, Azimuth.SE)


def is_line_sw(g: Gesture) -> bool:
    return _is_line_intercardinal(g, Azimuth.SW)


def is_line_nw(g: Gesture) -> bool:
    return _is_line_intercardinal(g, Azimuth.NW)


# =========================================
# Sub Intercardinal lines
# =========================================
def is_line_nne(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.NNE)


def is_line_ene(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.ENE)


def is_line_ese(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.ESE)


def is_line_sse(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.SSE)


def is_line_ssw(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.SSW)


def is_line_wsw(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.WSW)


def is_line_wnw(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.WNW)


def is_line_nnw(g: Gesture) -> bool:
    return _is_line_subintercardinal(g, Azimuth.NNW)


def _is_line_cardinal(g: Gesture, target: Azimuth, variance_deg=_CARDINAL_ANGLE_VARIANCE) -> bool:
    has_velocity = _has_velocity_in_direction(g, target)
    return _is_line(g, target, variance_deg, has_velocity)


def _is_line_intercardinal(g: Gesture, target: Azimuth, variance_deg=_INTERCARDINAL_ANGLE_VARIANCE) -> bool:
    target_1, target_2 = _SPLIT_SUBCARDINALS[target]
    has_velocity = _has_velocity_in_direction(g, target_1) or _has_velocity_in_direction(g, target_2)

    return _is_line(g, target, variance_deg, has_velocity)


def _is_line_subintercardinal(g: Gesture, target: Azimuth, variance_deg=_SUBINTERCARDINAL_ANGLE_VARIANCE) -> bool:
    target_1, target_2 = _SPLIT_SUBINTERCARDINALS[target]

    return _is_line_cardinal(g, target_1, variance_deg) or _is_line_intercardinal(g, target_2, variance_deg)


def _is_line(g: Gesture, target: Azimuth, variance_deg: float, has_velocity: bool) -> bool:
    has_azimuth = has_azimuth_in_range(g, target, variance_deg)

    # print(f"Gesture ({g.id}) {primary.name} line: velocity={has_velocity}, azimuth={has_azimuth}")
    return has_velocity and has_azimuth


# =========================================
# Utils
# =========================================
def _has_velocity_in_direction(g: Gesture, azimuth: Azimuth) -> bool:
    extremum = Extremum.from_azimuth(azimuth)
    iter = g.iter_x_extrema if extremum.is_x() else g.iter_y_extrema
    return equals_single(iter(), extremum)

    # if g._MIN_VELOCITY


def has_azimuth_in_range(g: Gesture, target: Azimuth, variance_deg) -> bool:
    angle = g.direction.get_azimuth()
    delta = ((angle - target.deg + 180.0) % 360.0) - 180.0
    return abs(delta) <= variance_deg + 1e-9
