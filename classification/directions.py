from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.vector_2 import Vector2


# =========================================
# Cardinal Directions
# =========================================
def is_direction_n(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.N)


def is_direction_e(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.E)


def is_direction_s(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.S)


def is_direction_w(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.W)


# =========================================
# Intercardinal Directions
# =========================================
def is_direction_ne(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.NE)


def is_direction_se(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.SE)


def is_direction_sw(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.SW)


def is_direction_nw(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.NW)


# =========================================
# Secondary Intercardinal Directions
# =========================================
def is_direction_nne(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.NNE)


def is_direction_ene(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.ENE)


def is_direction_ese(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.ESE)


def is_direction_sse(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.SSE)


def is_direction_ssw(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.SSW)


def is_direction_wsw(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.WSW)


def is_direction_wnw(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.WNW)


def is_direction_nnw(direction: Vector2) -> bool:
    return _is_direction_within_variance(direction, Azimuth.NNW)


# =========================================
# Utils
# =========================================
def _is_direction_within_variance(direction: Vector2, azimuth: Azimuth, variance_deg: float = 22.5) -> bool:
    bearing = direction.get_bearing()
    print(f"bearing: {bearing} | variance: +- {variance_deg}")
    return (azimuth.deg - variance_deg) <= bearing <= (azimuth.deg + variance_deg)
