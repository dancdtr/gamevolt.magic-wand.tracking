from classification.lines import has_azimuth_in_range
from detection.gesture import Gesture
from gamevolt.maths.azimuth import Azimuth

# =========================================
# Cardinal Directions
# =========================================
_CARDINAL_ANGLE_VARIANCE = 22.5


def has_azimuth_n(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.N, _CARDINAL_ANGLE_VARIANCE)


def has_azimuth_e(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.E, _CARDINAL_ANGLE_VARIANCE)


def has_azimuth_s(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.S, _CARDINAL_ANGLE_VARIANCE)


def has_azimuth_w(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.W, _CARDINAL_ANGLE_VARIANCE)
