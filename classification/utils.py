from itertools import cycle, islice
from typing import Iterable, Sequence

from classification.lines import is_line_e, is_line_n, is_line_s, is_line_w
from detection.gesture import Gesture
from detection.turn import TurnType
from detection.turn_direction import TurnDirection
from detection.turn_event import TurnEvent
from gamevolt.iterables.iter_tools import equals, matches_prefix
from gamevolt.maths.azimuth import Azimuth
from gamevolt.maths.extremum import Extremum

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


_MIN_LINE_DURATION = 0.15
_MAX_LINE_DURATION = 0.6
_MIN_ARC_DURATION = 0.25
_MAX_ARC_DURATION = 1
_LINE_FUNCS = {
    Azimuth.N: is_line_n,
    Azimuth.E: is_line_e,
    Azimuth.S: is_line_s,
    Azimuth.W: is_line_w,
}


def matches_x_extrema(g: Gesture, *targets: Extremum) -> bool:
    return matches_extrema(g.iter_x_extrema(), *targets)


def matches_y_extrema(g: Gesture, *targets: Extremum) -> bool:
    return matches_extrema(g.iter_y_extrema(), *targets)


def matches_extrema(extrema: Iterable[Extremum], *targets: Extremum) -> bool:
    return equals(extrema, targets)


def matches_x_turn_types(g: Gesture, *turn_types: TurnType) -> bool:
    return matches_turn_types(g.iter_x_turn_types(), *turn_types)


def matches_y_turn_types(g: Gesture, *turn_types: TurnType) -> bool:
    return matches_turn_types(g.iter_y_turn_types(), *turn_types)


def matches_turn_types(turn_types: Iterable[TurnType], *targets: TurnType) -> bool:
    return equals(turn_types, targets)


def is_turn_type(turn_point: TurnEvent | None, turn_type: TurnType) -> bool:
    return turn_point is not None and turn_point.type == turn_type


def matches_curve(g: Gesture, *pattern: TurnType) -> bool:
    return matches_prefix(g.iter_turn_types(), pattern, allow_tail_missing=1, allow_tail_extra=0)


def _matches_curve(
    g: Gesture,
    start: Azimuth,
    degrees: int,
    direction: TurnDirection,
    allow_head_missing: int = 0,
    allow_head_extra: int = 0,
    allow_tail_missing: int = 0,
    allow_tail_extra: int = 0,
) -> bool:
    pattern = list(_get_curve_turn_sequence(start, degrees, direction))
    src = list(g.iter_turn_types())

    return matches_prefix(
        src,
        pattern,
        allow_head_missing=allow_head_missing,
        allow_head_extra=allow_head_extra,
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


def is_line_and_arc_270_compound(
    g: Gesture,
    line_start: Azimuth,
    arc_start: Azimuth,
    direction: TurnDirection,
    arc_first: bool,
    split_time: float,
) -> bool:
    return is_line_and_arc_compound(g, line_start, arc_start, 270, direction, arc_first, split_time)


def is_line_and_arc_compound(
    g: Gesture,
    line_start: Azimuth,
    arc_start: Azimuth,
    degrees: int,
    direction: TurnDirection,
    arc_first: bool,
    split_time: float,
) -> bool:
    g_line, g_arc = g.split(split_time)
    if arc_first:
        g_line, g_arc = g_arc, g_line

    if _MIN_LINE_DURATION > g_line.duration or g_line.duration > _MAX_LINE_DURATION:
        print(f"Failed line: {g_line.duration}")
        return False

    if _MIN_ARC_DURATION > g_arc.duration or g_arc.duration > _MAX_ARC_DURATION:
        print(f"Failed arc: {g_arc.duration}")
        return False

    return _LINE_FUNCS[line_start](g_line) and _matches_curve(
        g=g_arc,
        start=arc_start,
        degrees=degrees,
        direction=direction,
        allow_head_missing=1,
        allow_tail_missing=1,
    )
