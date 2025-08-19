from itertools import cycle, islice
from typing import Sequence

from classification.bounces import has_bounce_e2w, has_bounce_n2s, has_bounce_s2n, has_bounce_w2e
from classification.classifiers.inflections import (
    ends_with_x_turn_type_e2w,
    ends_with_x_turn_type_w2e,
    ends_with_y_turn_type_n2s,
    ends_with_y_turn_type_s2n,
)
from classification.directions import has_azimuth_e, has_azimuth_n, has_azimuth_s, has_azimuth_w, is_direction_ese
from detection.gesture import Gesture
from detection.turn import TurnType
from detection.turn_direction import TurnDirection
from gamevolt.iterables.iter_tools import matches_prefix
from gamevolt.maths.azimuth import Azimuth

_CW_BASE: tuple[TurnType, ...] = (
    TurnType.E2W,
    TurnType.S2N,
    TurnType.W2E,
    TurnType.N2S,
)

_CCW_BASE: tuple[TurnType, ...] = (
    TurnType.W2E,
    TurnType.S2N,
    TurnType.E2W,
    TurnType.N2S,
)

_CW_CARDINAL_OFFSET = {
    Azimuth.N: 0,
    Azimuth.E: 1,
    Azimuth.S: 2,
    Azimuth.W: 3,
}

_CCW_CARDINAL_OFFSET = {
    Azimuth.N: 0,
    Azimuth.W: 1,
    Azimuth.S: 2,
    Azimuth.E: 3,
}


# =========================================
# Curves 180 CW
# =========================================
def is_curve_180_cw_start_n(g: Gesture) -> bool:
    return ends_with_x_turn_type_e2w(g) and has_azimuth_s(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.N) and has_azimuth_s(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.N) and has_bounce_e2w(g)
    return ends_with_x_turn_type_e2w(g) and has_bounce_e2w(g)


def is_curve_180_cw_start_e(g: Gesture) -> bool:
    return ends_with_y_turn_type_s2n(g) and has_azimuth_w(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.E) and has_azimuth_w(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.E) and has_bounce_s2n(g)
    return ends_with_y_turn_type_s2n(g) and has_bounce_s2n(g)


def is_curve_180_cw_start_s(g: Gesture) -> bool:
    return ends_with_x_turn_type_w2e(g) and has_azimuth_n(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.S) and has_azimuth_n(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.S) and has_bounce_w2e(g)
    return ends_with_x_turn_type_w2e(g) and has_bounce_w2e(g)


def is_curve_180_cw_start_w(g: Gesture) -> bool:
    return ends_with_y_turn_type_n2s(g) and has_azimuth_e(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.W) and has_azimuth_e(g.azimuth)
    return _is_curve_180_cw(g, start=Azimuth.W) and has_bounce_n2s(g)
    return ends_with_y_turn_type_n2s(g) and has_bounce_n2s(g)


# =========================================
# Curves 180 CCW
# =========================================
def is_curve_180_ccw_start_n(g: Gesture) -> bool:
    return ends_with_x_turn_type_w2e(g) and has_azimuth_s(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.N) and has_azimuth_s(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.N) and has_bounce_w2e(g)
    return ends_with_x_turn_type_w2e(g) and has_bounce_w2e(g)


def is_curve_180_ccw_start_e(g: Gesture) -> bool:
    return ends_with_y_turn_type_n2s(g) and has_azimuth_w(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.E) and has_azimuth_w(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.E) and has_bounce_n2s(g)
    return ends_with_y_turn_type_n2s(g) and has_bounce_n2s(g)


def is_curve_180_ccw_start_s(g: Gesture) -> bool:
    return ends_with_x_turn_type_e2w(g) and has_azimuth_n(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.S) and has_azimuth_n(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.S) and has_bounce_e2w(g)
    return ends_with_x_turn_type_e2w(g) and has_bounce_e2w(g)


def is_curve_180_ccw_start_w(g: Gesture) -> bool:
    return ends_with_y_turn_type_s2n(g) and has_azimuth_e(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.W) and has_azimuth_e(g.azimuth)
    return _is_curve_180_ccw(g, start=Azimuth.W) and has_bounce_s2n(g)
    return ends_with_y_turn_type_s2n(g) and has_bounce_s2n(g)


# =========================================
# Curves 270 CW
# =========================================
def is_curve_270_cw_start_n(g: Gesture) -> bool:
    return _is_curve_270_cw(g, start=Azimuth.N)


def is_curve_270_cw_start_e(g: Gesture) -> bool:
    return _is_curve_270_cw(g, start=Azimuth.E)


def is_curve_270_cw_start_s(g: Gesture) -> bool:
    return _is_curve_270_cw(g, start=Azimuth.S)


def is_curve_270_cw_start_w(g: Gesture) -> bool:
    return _is_curve_270_cw(g, start=Azimuth.W)


# =========================================
# Curves 270 CCW
# =========================================
def is_curve_270_ccw_start_n(g: Gesture) -> bool:
    return _is_curve_270_ccw(g, start=Azimuth.N)


def is_curve_270_ccw_start_e(g: Gesture) -> bool:
    return _is_curve_270_ccw(g, start=Azimuth.E)


def is_curve_270_ccw_start_s(g: Gesture) -> bool:
    return _is_curve_270_ccw(g, start=Azimuth.S)


def is_curve_270_ccw_start_w(g: Gesture) -> bool:
    return _is_curve_270_ccw(g, start=Azimuth.W)


# =========================================
# Curves 360 CW
# =========================================
def is_curve_360_cw_start_n(g: Gesture) -> bool:
    return _is_curve_360_cw(g, start=Azimuth.N)


def is_curve_360_cw_start_e(g: Gesture) -> bool:
    return _is_curve_360_cw(g, start=Azimuth.E)


def is_curve_360_cw_start_s(g: Gesture) -> bool:
    return _is_curve_360_cw(g, start=Azimuth.S)


def is_curve_360_cw_start_w(g: Gesture) -> bool:
    return _is_curve_360_cw(g, start=Azimuth.W)


# =========================================
# Curves 360 CCW
# =========================================
def is_curve_360_ccw_start_n(g: Gesture) -> bool:
    return _is_curve_360_ccw(g, start=Azimuth.N)


def is_curve_360_ccw_start_e(g: Gesture) -> bool:
    return _is_curve_360_ccw(g, start=Azimuth.E)


def is_curve_360_ccw_start_s(g: Gesture) -> bool:
    return _is_curve_360_ccw(g, start=Azimuth.S)


def is_curve_360_ccw_start_w(g: Gesture) -> bool:
    return _is_curve_360_ccw(g, start=Azimuth.W)


# =========================================
# Utils
# =========================================
def _is_curve_360_cw(g: Gesture, start: Azimuth) -> bool:
    return _is_curve_360(g, start, direction=TurnDirection.CW)


def _is_curve_360_ccw(g: Gesture, start: Azimuth) -> bool:
    return _is_curve_360(g, start, direction=TurnDirection.CCW)


def _is_curve_270_cw(g: Gesture, start: Azimuth) -> bool:
    return _is_curve_270(g, start, direction=TurnDirection.CW)


def _is_curve_270_ccw(g: Gesture, start: Azimuth) -> bool:
    return _is_curve_270(g, start, direction=TurnDirection.CCW)


def _is_curve_180_cw(g: Gesture, start: Azimuth) -> bool:
    return _is_curve_180(g, start, direction=TurnDirection.CW)


def _is_curve_180_ccw(g: Gesture, start: Azimuth) -> bool:
    return _is_curve_180(g, start, direction=TurnDirection.CCW)


def _is_curve_360(g: Gesture, start: Azimuth, direction: TurnDirection) -> bool:
    return _matches_curve(g=g, start=start, degrees=360, direction=direction, allow_tail_missing=1)


def _is_curve_270(g: Gesture, start: Azimuth, direction: TurnDirection) -> bool:
    return _matches_curve(g=g, start=start, degrees=270, direction=direction, allow_tail_missing=1)


def _is_curve_180(g: Gesture, start: Azimuth, direction: TurnDirection) -> bool:
    return _matches_curve(g=g, start=start, degrees=180, direction=direction, allow_tail_missing=1)


def _matches_curve(
    g: Gesture,
    start: Azimuth,
    degrees: int,
    direction: TurnDirection,
    allow_tail_missing: int = 0,
    allow_tail_extra: int = 0,
) -> bool:
    pattern = _get_curve_turn_sequence(start, degrees, direction)
    src = g.iter_turn_types()
    return matches_prefix(
        src,
        pattern,
        allow_tail_missing=allow_tail_missing,
        allow_tail_extra=allow_tail_extra,
    )


def _get_curve_turn_sequence(start: Azimuth, degrees: int, direction: TurnDirection) -> tuple[TurnType, ...]:
    if start not in _CW_CARDINAL_OFFSET:
        raise ValueError(f"start must be cardinal (N/E/S/W), got {start.name}")
    if degrees % 90 != 0:
        raise ValueError(f"degrees must be a multiple of 90, got {degrees}")

    steps = degrees // 90
    base = _CW_BASE if direction is TurnDirection.CW else _CCW_BASE
    cardinal_offset = _CW_CARDINAL_OFFSET if direction is TurnDirection.CW else _CCW_CARDINAL_OFFSET
    rotated = _rotate(base, cardinal_offset[start])

    return tuple(islice(cycle(rotated), steps))


def _rotate(seq: Sequence[TurnType], k: int) -> tuple[TurnType, ...]:
    s = tuple(seq)
    k %= len(s)
    return s[k:] + s[:k]
