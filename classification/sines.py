from enum import Enum, auto
from typing import Sequence

from classification.directions import has_azimuth_e, has_azimuth_n, has_azimuth_s, has_azimuth_w
from classification.gesture_type import GestureType
from detection.gesture import Gesture
from detection.turn import TurnType
from detection.turn_direction import TurnDirection
from detection.turn_event import TurnEvent
from gamevolt.iterables.iter_tools import matches_prefix, take_infinite
from gamevolt.maths.azimuth import Azimuth


class SineType(Enum):
    N = auto()
    E = auto()
    S = auto()
    W = auto()
    NEG_N = auto()
    NEG_E = auto()
    NEG_S = auto()
    NEG_W = auto()


class Period(Enum):
    SINE_180 = auto()
    SINE_360 = auto()
    SINE_540 = auto()
    SINE_720 = auto()


_DIRECTIONS = {
    Azimuth.N: has_azimuth_n,
    Azimuth.E: has_azimuth_e,
    Azimuth.S: has_azimuth_s,
    Azimuth.W: has_azimuth_w,
}

_TURN_POINTS = {
    SineType.N: [TurnType.W2E, TurnType.E2W],
    SineType.E: [TurnType.N2S, TurnType.S2N],
    SineType.S: [TurnType.E2W, TurnType.W2E],
    SineType.W: [TurnType.S2N, TurnType.N2S],
    SineType.NEG_N: [TurnType.E2W, TurnType.W2E],
    SineType.NEG_E: [TurnType.S2N, TurnType.N2S],
    SineType.NEG_S: [TurnType.W2E, TurnType.E2W],
    SineType.NEG_W: [TurnType.N2S, TurnType.S2N],
}

_PERIOD_COUNT = {
    Period.SINE_180: 1,
    Period.SINE_360: 2,
    Period.SINE_540: 3,
    Period.SINE_720: 4,
}


# =========================================
# Sines 360
# =========================================
def is_wave_sine_n_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.N, SineType.N)


def is_wave_sine_e_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.E, SineType.E)


def is_wave_sine_s_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.S, SineType.S)


def is_wave_sine_w_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.W, SineType.W)


# =========================================
# Negative Sines 360
# =========================================
def is_wave_negative_sine_n_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.N, SineType.NEG_N)


def is_wave_negative_sine_e_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.E, SineType.NEG_E)


def is_wave_negative_sine_s_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.S, SineType.NEG_S)


def is_wave_negative_sine_w_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, Azimuth.W, SineType.NEG_W)


# =========================================
# Sines 540
# =========================================
def is_wave_sine_n_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.N, SineType.N)


def is_wave_sine_e_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.E, SineType.E)


def is_wave_sine_s_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.S, SineType.S)


def is_wave_sine_w_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.W, SineType.W)


# =========================================
# Negative Sines 540
# =========================================
def is_wave_negative_sine_n_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.N, SineType.NEG_N)


def is_wave_negative_sine_e_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.E, SineType.NEG_E)


def is_wave_negative_sine_s_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.S, SineType.NEG_S)


def is_wave_negative_sine_w_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, Azimuth.W, SineType.NEG_W)


# =========================================
# Utils
# =========================================
def _is_wave_sine_540(g: Gesture, direction: Azimuth, sine_type: SineType) -> bool:
    return _is_wave_sign(g, direction, sine_type, Period.SINE_540)


def _is_wave_sine_360(g: Gesture, direction: Azimuth, sine_type: SineType) -> bool:
    return _is_wave_sign(g, direction, sine_type, Period.SINE_360)


def _is_wave_sign(g: Gesture, direction: Azimuth, sine_type: SineType, period: Period) -> bool:
    iter_turn_points = g.iter_x_turn_points() if direction in [Azimuth.N, Azimuth.S] else g.iter_y_turn_points()

    period_count = _PERIOD_COUNT[period]
    targets = list(take_infinite(period_count, _TURN_POINTS[sine_type]))

    # print(f"Actual: {[t.name for t in iter_turn_points]}")
    # print(f"Expected: {[t.name for t in targets]}")

    a = matches_prefix(iter_turn_points, targets, allow_head_extra=2)
    b = _DIRECTIONS[direction](g)

    print(f"Matches curve: {a} | has direction: {b}")

    return a and b
