from classification.azimuth import Azimuth
from classification.extremum import Extremum
from detection.gesture import Gesture
from gamevolt.iterables.iter_tools import equals_single


# =========================================
# Cardinal velocities
# =========================================
def is_velocity_n(g: Gesture) -> bool:
    return _has_sufficient_velocity(g, Azimuth.N)


def is_velocity_e(g: Gesture) -> bool:
    return _has_sufficient_velocity(g, Azimuth.E)


def is_velocity_s(g: Gesture) -> bool:
    return _has_sufficient_velocity(g, Azimuth.S)


def is_velocity_w(g: Gesture) -> bool:
    return _has_sufficient_velocity(g, Azimuth.W)


# =========================================
# Intercardinal velocities
# =========================================
def is_velocity_ne(g: Gesture) -> bool:
    return is_velocity_n(g) and is_velocity_e(g)


def is_velocity_se(g: Gesture) -> bool:
    return is_velocity_s(g) and is_velocity_e(g)


def is_velocity_sw(g: Gesture) -> bool:
    return is_velocity_s(g) and is_velocity_w(g)


def is_velocity_nw(g: Gesture) -> bool:
    return is_velocity_n(g) and is_velocity_w(g)


# =========================================
# Secondary Intercardinal velocities
# =========================================
def is_velocity_nne(g: Gesture) -> bool:
    return is_velocity_ne(g) or is_velocity_n(g)


def is_velocity_ene(g: Gesture) -> bool:
    return is_velocity_ne(g) or is_velocity_e(g)


def is_velocity_ese(g: Gesture) -> bool:
    return is_velocity_se(g) and is_velocity_e(g)


def is_velocity_sse(g: Gesture) -> bool:
    return is_velocity_se(g) and is_velocity_s(g)


def is_velocity_ssw(g: Gesture) -> bool:
    return is_velocity_sw(g) and is_velocity_s(g)


def is_velocity_wsw(g: Gesture) -> bool:
    return is_velocity_sw(g) and is_velocity_w(g)


def is_velocity_wnw(g: Gesture) -> bool:
    return is_velocity_nw(g) or is_velocity_w(g)


def is_velocity_nnw(g: Gesture) -> bool:
    return is_velocity_nw(g) or is_velocity_n(g)


# =========================================
# Utils
# =========================================
def _has_sufficient_velocity(g: Gesture, azimuth: Azimuth) -> bool:
    extremum = Extremum.from_azimuth(azimuth)
    iter = g.iter_x_extrema if extremum.is_x() else g.iter_y_extrema
    return equals_single(iter(), extremum)
