from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.vector_2 import Vector2

# =========================================
# Cardinal Directions
# =========================================


def has_azimuth_n(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.N)


def has_azimuth_e(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.E)


def has_azimuth_s(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.S)


def has_azimuth_w(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.W)


# =========================================
# Intercardinal Directions
# =========================================
def has_azimuth_ne(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.NE)


def has_azimuth_se(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.SE)


def has_azimuth_sw(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.SW)


def has_azimuth_nw(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.NW)


# =========================================
# Secondary Intercardinal Directions
# =========================================
def is_direction_nne(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.NNE)


def is_direction_ene(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.ENE)


def is_direction_ese(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.ESE)


def is_direction_sse(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.SSE)


def is_direction_ssw(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.SSW)


def is_direction_wsw(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.WSW)


def is_direction_wnw(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.WNW)


def is_direction_nnw(direction: Vector2) -> bool:
    return _has_azimuth(direction, Azimuth.NNW)


# =========================================
# Utils
# =========================================
def _has_azimuth(direction: Vector2, azimuth: Azimuth, variance_deg: float = 22.5) -> bool:
    bearing = direction.get_bearing()
    print(f"bearing: {bearing} | variance: +- {variance_deg}")
    return (azimuth.deg - variance_deg) <= bearing <= (azimuth.deg + variance_deg)
