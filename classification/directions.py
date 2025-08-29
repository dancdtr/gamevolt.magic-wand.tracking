from classification.utils import has_azimuth_in_range
from detection.gesture import Gesture
from gamevolt.maths.azimuth import Azimuth

# =========================================
# Cardinal Directions
# =========================================


def has_azimuth_n(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.N)


def has_azimuth_e(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.E)


def has_azimuth_s(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.S)


def has_azimuth_w(g: Gesture) -> bool:
    return has_azimuth_in_range(g, Azimuth.W)
