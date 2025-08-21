from classification.utils import matches_x_extrema, matches_y_extrema
from detection.gesture import Gesture
from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.extremum import Extremum


# =========================================
# Bounces
# =========================================
def has_bounce_n2s(g: Gesture) -> bool:
    return has_bounce(g, Azimuth.N, Azimuth.S)

def has_bounce_e2w(g: Gesture) -> bool:
    return has_bounce(g, Azimuth.E, Azimuth.W)

def has_bounce_s2n(g: Gesture) -> bool:
    return has_bounce(g, Azimuth.S, Azimuth.N)

def has_bounce_w2e(g: Gesture) -> bool:
    return has_bounce(g, Azimuth.W, Azimuth.E)

def has_bounce(g: Gesture, towards: Azimuth, backwards: Azimuth) -> bool:
        match towards, backwards:
            case Azimuth.N, Azimuth.S: return matches_y_extrema(g, Extremum.Y_MAX, Extremum.Y_MIN)
            case Azimuth.E, Azimuth.W: return matches_x_extrema(g, Extremum.X_MAX, Extremum.X_MIN)
            case Azimuth.S, Azimuth.N: return matches_y_extrema(g, Extremum.Y_MIN, Extremum.Y_MAX)
            case Azimuth.W, Azimuth.E: return matches_x_extrema(g, Extremum.X_MIN, Extremum.X_MAX)
            case _: raise ValueError(f"No bounce defined for {towards.name} / {backwards.name}.")

