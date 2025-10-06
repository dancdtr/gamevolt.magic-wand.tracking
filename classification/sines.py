from enum import Enum, auto

from classification.directions import CardinalDirection, is_moving_e, is_moving_n, is_moving_s, is_moving_w
from gamevolt.iterables.iter_tools import matches_prefix, take_infinite
from gestures.gesture import Gesture
from gestures.turn_type import TurnType


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
    CardinalDirection.N: is_moving_n,
    CardinalDirection.E: is_moving_e,
    CardinalDirection.S: is_moving_s,
    CardinalDirection.W: is_moving_w,
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
    return _is_wave_sine_360(g, CardinalDirection.N, SineType.N)


def is_wave_sine_e_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, CardinalDirection.E, SineType.E)


def is_wave_sine_s_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, CardinalDirection.S, SineType.S)


def is_wave_sine_w_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, CardinalDirection.W, SineType.W)


# =========================================
# Negative Sines 360
# =========================================
def is_wave_negative_sine_n_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, CardinalDirection.N, SineType.NEG_N)


def is_wave_negative_sine_e_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, CardinalDirection.E, SineType.NEG_E)


def is_wave_negative_sine_s_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, CardinalDirection.S, SineType.NEG_S)


def is_wave_negative_sine_w_360(g: Gesture) -> bool:
    return _is_wave_sine_360(g, CardinalDirection.W, SineType.NEG_W)


# =========================================
# Sines 540
# =========================================
def is_wave_sine_n_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.N, SineType.N)


def is_wave_sine_e_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.E, SineType.E)


def is_wave_sine_s_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.S, SineType.S)


def is_wave_sine_w_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.W, SineType.W)


# =========================================
# Negative Sines 540
# =========================================
def is_wave_negative_sine_n_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.N, SineType.NEG_N)


def is_wave_negative_sine_e_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.E, SineType.NEG_E)


def is_wave_negative_sine_s_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.S, SineType.NEG_S)


def is_wave_negative_sine_w_540(g: Gesture) -> bool:
    return _is_wave_sine_540(g, CardinalDirection.W, SineType.NEG_W)


# =========================================
# Sines 720
# =========================================
def is_wave_sine_n_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.N, SineType.N)


def is_wave_sine_e_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.E, SineType.E)


def is_wave_sine_s_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.S, SineType.S)


def is_wave_sine_w_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.W, SineType.W)


# =========================================
# Negative Sines 720
# =========================================
def is_wave_negative_sine_n_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.N, SineType.NEG_N)


def is_wave_negative_sine_e_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.E, SineType.NEG_E)


def is_wave_negative_sine_s_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.S, SineType.NEG_S)


def is_wave_negative_sine_w_720(g: Gesture) -> bool:
    return _is_wave_sine_720(g, CardinalDirection.W, SineType.NEG_W)


# =========================================
# Utils
# =========================================


def _is_wave_sine_360(g: Gesture, direction: CardinalDirection, sine_type: SineType) -> bool:
    return _is_wave_sine(g, direction, sine_type, Period.SINE_360)


def _is_wave_sine_540(g: Gesture, direction: CardinalDirection, sine_type: SineType) -> bool:
    return _is_wave_sine(g, direction, sine_type, Period.SINE_540)


def _is_wave_sine_720(g: Gesture, direction: CardinalDirection, sine_type: SineType) -> bool:
    return _is_wave_sine(g, direction, sine_type, Period.SINE_720)


def _is_wave_sine(g: Gesture, direction: CardinalDirection, sine_type: SineType, period: Period) -> bool:
    iter_turn_points = g.iter_x_turn_points() if direction in [CardinalDirection.N, CardinalDirection.S] else g.iter_y_turn_points()

    period_count = _PERIOD_COUNT[period]
    targets = list(take_infinite(period_count, _TURN_POINTS[sine_type]))

    # print(f"Actual: {[t.name for t in iter_turn_points]}")
    # print(f"Expected: {[t.name for t in targets]}")

    a = matches_prefix(iter_turn_points, targets, allow_head_extra=2)
    b = _DIRECTIONS[direction](g)

    # print(f"Matches curve: {a} | has direction: {b}")

    return a and b
