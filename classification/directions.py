from detection.gesture import Gesture
from gamevolt.maths.azimuth import Azimuth

# =========================================
# Cardinal Directions
# =========================================


def has_azimuth_n(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.N)


def has_azimuth_e(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.E)


def has_azimuth_s(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.S)


def has_azimuth_w(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.W)


# =========================================
# Intercardinal Directions
# =========================================
def has_azimuth_ne(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.NE)


def has_azimuth_se(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.SE)


def has_azimuth_sw(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.SW)


def has_azimuth_nw(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.NW)


# =========================================
# Sub Intercardinal Directions
# =========================================
def is_direction_nne(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.NNE)


def is_direction_ene(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.ENE)


def is_direction_ese(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.ESE)


def is_direction_sse(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.SSE)


def is_direction_ssw(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.SSW)


def is_direction_wsw(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.WSW)


def is_direction_wnw(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.WNW)


def is_direction_nnw(g: Gesture) -> bool:
    return _has_azimuth_in_range(g, Azimuth.NNW)


# =========================================
# Utils
# =========================================
def _has_azimuth_in_range(g: Gesture, target: Azimuth, variance_deg: float = 22.5) -> bool:
    angle = g.direction.get_azimuth()
    delta = ((angle - target.deg + 180.0) % 360.0) - 180.0
    return abs(delta) <= variance_deg + 1e-9
