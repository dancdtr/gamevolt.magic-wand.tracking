from collections import deque
from collections.abc import Callable, Iterator
from enum import Enum, auto
from itertools import islice, zip_longest
from typing import Iterable, Sequence, TypeVar

from classification.extremum import Extremum as E
from classification.gesture_classifier_mask import GestureClassifierMask
from classification.gesture_type import GestureType as G
from detection.gesture import Gesture
from detection.turn import TurnType
from detection.turn_point import TurnPoint

T = TypeVar("T")
_SENTINEL = object()

# ---------- Primitive comparisons ----------

def iter_equal(a: Iterable[T], b: Iterable[T]) -> bool:
    return all(x == y for x, y in zip_longest(a, b, fillvalue=_SENTINEL))


def iter_is(a: Iterable[T], b: Iterable[T]) -> bool:
    for x, y in zip_longest(a, b, fillvalue=_SENTINEL):
        if x is not y:
            return False
    return True

# ---------- Lazy cropping helpers ----------

def drop_first(it: Iterable[T], n: int) -> Iterator[T]:
    """Yield all but the first n items (lazy, no extra memory)."""
    return islice(it, n, None)

def drop_last(it: Iterable[T], n: int) -> Iterator[T]:
    """Yield all but the last n items (lazy, O(n) buffer)."""
    if n <= 0:
        yield from it
        return
    q: deque[T] = deque(maxlen=n)
    for x in it:
        if len(q) == q.maxlen:
            yield q.popleft()
        q.append(x)

# ---------- Prefix match with controlled tail slack ----------

def matches_prefix(
    it: Iterable[T],
    prefix: Sequence[T],               # pattern is small; materialize ok
    *,
    skip_head: int = 0,                # drop N leading items first
    max_tail_extra: int | None = 0  # None = unlimited, 0 = exact, N = allow up to N extras
) -> bool:
    it = iter(it)
    if skip_head:
        it = islice(it, skip_head, None)

    # compare against prefix
    for want in prefix:
        got = next(it, _SENTINEL)
        if got is _SENTINEL or got is not want:
            return False

    # enforce tail allowance
    if max_tail_extra is None:
        return True  # unlimited extras allowed
    if max_tail_extra <= 0:
        return next(it, _SENTINEL) is _SENTINEL  # must end here

    # allow up to N extras, but not more
    for _ in range(max_tail_extra):
        if next(it, _SENTINEL) is _SENTINEL:
            return True  # ended within allowance
    return next(it, _SENTINEL) is _SENTINEL  # no (N+1)th extra

T = TypeVar("T")

def matches_suffix(
    it: Iterable[T],
    suffix: Sequence[T],
    *,
    skip_head: int = 0,                 # drop first K items
    drop_tail: int = 0,                 # ignore last K items
    max_head_extra: int | None = 0,  # None = unlimited extras before suffix
) -> bool:
    """
    True iff, after skipping 'skip_head' items and dropping 'drop_tail' items
    from the end, the iterable ends with 'suffix'. Uses identity ('is') semantics
    if T are enums; change to '==' if you want equality.
    """
    # Fast path for empty suffix
    m = len(suffix)
    if m == 0:
        # After cropping, anything ends with empty suffix. Enforce head-extra limit if provided.
        if max_head_extra is None:
            return True
        # Need the cropped length to check extras; count lazily:
        cnt = 0
        for _ in islice(it, skip_head, None):
            cnt += 1
        cnt = max(0, cnt - drop_tail)
        return cnt <= max_head_extra

    # Skip the head lazily
    it = islice(it, skip_head, None)

    # Maintain a bounded deque of the last (m + drop_tail) items
    deq = deque(maxlen=m + max(drop_tail, 0))
    cnt = 0
    for x in it:
        deq.append(x)
        cnt += 1

    # Drop the tail items (if any)
    for _ in range(min(drop_tail, len(deq))):
        deq.pop()

    # Now deq holds the effective tail to check
    if len(deq) < m:
        return False

    # Check head-extras allowance
    effective_len = min(cnt, cnt - drop_tail)  # total after drop_tail (bounded at 0)
    extras_before_suffix = effective_len - m
    if extras_before_suffix < 0:
        return False
    if max_head_extra is not None and extras_before_suffix > max_head_extra:
        return False

    # Compare the last m items to the suffix (identity check for enums)
    # islice over deque avoids materializing a list
    start = len(deq) - m
    for got, want in zip(islice(deq, start, None), suffix):
        if got is not want:   # use '!=' if you want equality semantics
            return False
    return True

def matches(iterable: Iterable[T], *values: T) -> bool:
    return iter_is(iterable, values)


class Azimuth(Enum):
    N = auto()
    E = auto()
    S = auto()
    W = auto()
    NE = auto()
    SE = auto()
    SW = auto()
    NW = auto()
    NNE = auto()
    ENE = auto()
    ESE = auto()
    SSE = auto()
    SSW = auto()
    WSW = auto()
    WNW = auto()
    NNW = auto()


azimuth_angles: dict[Azimuth, float] = {
    Azimuth.N: 0,
    Azimuth.E: 90,
    Azimuth.S: 180,
    Azimuth.W: 270,
    Azimuth.NE: 45,
    Azimuth.SE: 135,
    Azimuth.SW: 225,
    Azimuth.NW: 315,
    Azimuth.NNE: 22.5,
    Azimuth.ENE: 67.5,
    Azimuth.ESE: 112.5,
    Azimuth.SSE: 157.5,
    Azimuth.SSW: 202.5,
    Azimuth.WSW: 247.5,
    Azimuth.WNW: 292.5,
    Azimuth.NNW: 337.5,
}


class GestureClassifier:
    def __init__(self) -> None:
        self._classifiers: dict[G, Callable[[Gesture], bool]] = {
            G.UP: is_up,
            G.RIGHT: is_right,
            G.DOWN: is_down,
            G.LEFT: is_left,
            G.UP_RIGHT: is_up_right,
            G.DOWN_RIGHT: is_down_right,
            G.DOWN_LEFT: is_down_left,
            G.UP_LEFT: is_up_left,
            G.UP_VIA_RIGHT_SEMI: is_up_via_right_semi,
            G.UP_VIA_LEFT_SEMI: is_up_via_left_semi,
            G.DOWN_VIA_RIGHT_SEMI: is_down_via_right_semi,
            G.DOWN_VIA_LEFT_SEMI: is_down_via_left_semi,
            G.RIGHT_VIA_UP_SEMI: is_right_via_up_semi,
            G.LEFT_VIA_UP_SEMI: is_left_via_up_semi,
            G.RIGHT_VIA_DOWN_SEMI: is_right_via_down_semi,
            G.LEFT_VIA_DOWN_SEMI: is_left_via_down_semi,
            G.LEFT_START_CW_CIRCLE: is_left_start_cw_circle,
            G.UP_START_CW_CIRCLE: is_up_start_cw_circle,
            G.RIGHT_START_CW_CIRCLE: is_right_start_cw_circle,
            G.DOWN_START_CW_CIRCLE: is_down_start_cw_circle,
            G.LEFT_START_CCW_CIRCLE: is_left_start_ccw_circle,
            G.UP_START_CCW_CIRCLE: is_up_start_ccw_circle,
            G.RIGHT_START_CCW_CIRCLE: is_right_start_ccw_circle,
            G.DOWN_START_CCW_CIRCLE: is_down_start_ccw_circle,
        }

    def classify(self, gesture: Gesture, mask: GestureClassifierMask | None = None) -> G:

        print(f"Extrema: {[e.name for e in gesture.extrema]}")
        print(f"X extrema: {[e.name for e in gesture.iter_x_extrema()]}")
        print(f"Y extrema: {[e.name for e in gesture.iter_y_extrema()]}")
        print(f"Turn points: {[tp.type.name for tp in gesture.turn_points]}")

        if mask is None:
            return self._classify_any(gesture)

        for target in mask.target_gesture_types:
            classifier = self._get_classifier(target)
            if classifier(gesture):
                return target

        return G.UNKNOWN

    def _get_classifier(self, type: G):
        classifier = self._classifiers[type]
        if not classifier:
            raise Exception(f"No classifier set for {G.name}!")
        return classifier

    def _classify_any(self, gesture) -> G:
        gesture_type = G.UNKNOWN

        # check circles
        if is_up_start_cw_circle(gesture):
            return G.UP_START_CW_CIRCLE
        if is_right_start_cw_circle(gesture):
            return G.RIGHT_START_CW_CIRCLE
        if is_down_start_cw_circle(gesture):
            return G.DOWN_START_CW_CIRCLE
        if is_left_start_cw_circle(gesture):
            return G.LEFT_START_CW_CIRCLE
        if is_up_start_ccw_circle(gesture):
            return G.UP_START_CCW_CIRCLE
        if is_right_start_ccw_circle(gesture):
            return G.RIGHT_START_CCW_CIRCLE
        if is_down_start_ccw_circle(gesture):
            return G.DOWN_START_CCW_CIRCLE
        if is_left_start_ccw_circle(gesture):
            return G.LEFT_START_CCW_CIRCLE

        # check intercardinals
        # if is_up_right_diagonal(gesture):
        #     return G.UP_RIGHT
        # if is_down_right_diagonal(gesture):
        #     return G.DOWN_RIGHT
        # if is_down_left_diagonal(gesture):
        #     return G.DOWN_LEFT
        # if is_up_left_diagonal(gesture):
        #     return G.UP_LEFT

        # check subintercardinals
        # if is_north_north_east(gesture):
        #     return G.NNE
        # if is_east_north_east(gesture):
        #     return G.ENE
        # if is_east_south_east(gesture):
        #     return G.ESE
        # if is_south_south_east(gesture):
        #     return G.SSE
        # if is_south_south_west(gesture):
        #     return G.SSW
        # if is_west_south_west(gesture):
        #     return G.WSW
        # if is_west_north_west(gesture):
        #     return G.WNW
        # if is_north_north_west(gesture):
        #     return G.NNW

        # check semi circles
        # if is_up_via_left_semi(gesture):
        #     return G.UP_VIA_LEFT_SEMI
        # if is_up_via_right_semi(gesture):
        #     return G.UP_VIA_RIGHT_SEMI
        # if is_right_via_up_semi(gesture):
        #     return G.RIGHT_VIA_UP_SEMI
        # if is_right_via_down_semi(gesture):
        #     return G.RIGHT_VIA_DOWN_SEMI
        # if is_down_via_right_semi(gesture):
        #     return G.DOWN_VIA_RIGHT_SEMI
        # if is_down_via_left_semi(gesture):
        #     return G.DOWN_VIA_LEFT_SEMI
        # if is_left_via_up_semi(gesture):
        #     return G.LEFT_VIA_UP_SEMI
        # if is_left_via_down_semi(gesture):
        #     return G.LEFT_VIA_DOWN_SEMI

        # check cardinals
        # if is_up(gesture):
        #     return G.UP
        # if is_right(gesture):
        #     return G.RIGHT
        # if is_down(gesture):
        #     return G.DOWN
        # if is_left(gesture):
        #     return G.LEFT

        return gesture_type


def is_circle(gesture: Gesture, turn_types: list[TurnType]) -> bool:
    return is_curve(gesture, turn_types, allow_overshoot=True)


def is_curve(gesture: Gesture, turn_types: Iterable[TurnType], allow_overshoot: bool) -> bool:
    if matches_turn_types(gesture.iter_turn_types(), *turn_types):
    if turn_types == gesture.iter_turn_types:
        return True
    elif allow_overshoot:
        return turn_types[:-1] == gesture.iter_turn_types
    return False

def is_curve_prefix(
    gesture: Gesture,
    *pattern: TurnType,
    skip_head: int = 0,
    max_tail_extra: int | None = 0,  # None = unlimited
) -> bool:
    return matches_prefix(gesture.iter_turn_types(),pattern,skip_head=skip_head, max_tail_extra=max_tail_extra)

def is_curve_exact(gesture: Gesture, *pattern: TurnType, drop_head: int = 0, drop_tail: int = 0) -> bool:
    src = gesture.iter_turn_types()
    if drop_head:
        src = drop_first(src, drop_head)
    if drop_tail:
        src = drop_last(src, drop_tail)
    return iter_is(src, pattern)

def is_up_start_cw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN])


def is_right_start_cw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT])


def is_down_start_cw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.LEFT_TO_RIGHT, TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP])


def is_left_start_cw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.UP_TO_DOWN, TurnType.RIGHT_TO_LEFT, TurnType.DOWN_TO_UP, TurnType.LEFT_TO_RIGHT])


def is_up_start_ccw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN])


def is_right_start_ccw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT])


def is_down_start_ccw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT, TurnType.DOWN_TO_UP])


def is_left_start_ccw_circle(gesture: Gesture) -> bool:
    return is_circle(gesture, [TurnType.DOWN_TO_UP, TurnType.RIGHT_TO_LEFT, TurnType.UP_TO_DOWN, TurnType.LEFT_TO_RIGHT])


def is_up_via_right_semi(gesture: Gesture) -> bool:
    return is_up(gesture) and is_right_left_curve(gesture)


def is_up_via_left_semi(gesture: Gesture) -> bool:
    return is_up(gesture) and is_left_right_curve(gesture)


def is_right_via_up_semi(gesture: Gesture) -> bool:
    return is_right(gesture) and is_up_down_curve(gesture)


def is_right_via_down_semi(gesture: Gesture) -> bool:
    return is_right(gesture) and is_down_up_curve(gesture)


def is_down_via_right_semi(gesture: Gesture) -> bool:
    return is_down(gesture) and is_right_left_curve(gesture)


def is_down_via_left_semi(gesture: Gesture) -> bool:
    return is_down(gesture) and is_left_right_curve(gesture)


def is_left_via_up_semi(gesture: Gesture) -> bool:
    return is_left(gesture) and is_up_down_curve(gesture)


def is_left_via_down_semi(gesture: Gesture) -> bool:
    return is_left(gesture) and is_down_up_curve(gesture)


def is_up_right_diagonal(gesture: Gesture) -> bool:
    return is_up_right(gesture) and is_diagonal(gesture, Azimuth.NE)


def is_down_right_diagonal(gesture: Gesture) -> bool:
    return is_down_right(gesture) and is_diagonal(gesture, Azimuth.SE)


def is_down_left_diagonal(gesture: Gesture) -> bool:
    return is_down_left(gesture) and is_diagonal(gesture, Azimuth.SW)


def is_up_left_diagonal(gesture: Gesture) -> bool:
    return is_up_left(gesture) and is_diagonal(gesture, Azimuth.NW)


def is_north_north_east(gesture: Gesture) -> bool:
    return (is_up_right(gesture) or is_up(gesture)) and is_diagonal(gesture, Azimuth.NNE)


def is_east_north_east(gesture: Gesture) -> bool:
    return (is_up_right(gesture) or is_right(gesture)) and is_diagonal(gesture, Azimuth.ENE)


def is_east_south_east(gesture: Gesture) -> bool:
    return (is_down_right(gesture) or is_right(gesture)) and is_diagonal(gesture, Azimuth.ESE)


def is_south_south_east(gesture: Gesture) -> bool:
    return (is_down_right(gesture) or is_down(gesture)) and is_diagonal(gesture, Azimuth.SSE)


def is_south_south_west(gesture: Gesture) -> bool:
    return (is_down_left(gesture) or is_down(gesture)) and is_diagonal(gesture, Azimuth.SSW)


def is_west_south_west(gesture: Gesture) -> bool:
    return (is_down_left(gesture) or is_left(gesture)) and is_diagonal(gesture, Azimuth.WSW)


def is_west_north_west(gesture: Gesture) -> bool:
    return (is_up_left(gesture) or is_left(gesture)) and is_diagonal(gesture, Azimuth.WNW)


def is_north_north_west(gesture: Gesture) -> bool:
    return (is_up_left(gesture) or is_up(gesture)) and is_diagonal(gesture, Azimuth.NNW)


def is_diagonal(gesture: Gesture, azimuth: Azimuth, variance_deg: float = 22.5) -> bool:
    angle = azimuth_angles.get(azimuth)
    if angle is None:
        raise Exception(f"Azimuth '{azimuth.name}' is not defined!")

    bearing = gesture.direction.get_bearing()
    print(f"bearing: {bearing} | variance: +- {variance_deg}")
    return (angle - variance_deg) <= bearing <= (angle + variance_deg)


def is_up_right(gesture: Gesture) -> bool:
    return (
        gesture.direction.x < 0 and gesture.direction.y < 0 and matches_x_extrema(gesture, E.X_MAX) and matches_y_extrema(gesture, E.Y_MAX)
    )


def is_down_right(gesture: Gesture) -> bool:
    return (
        gesture.direction.x < 0 and gesture.direction.y > 0 and matches_x_extrema(gesture, E.X_MAX) and matches_y_extrema(gesture, E.Y_MIN)
    )


def is_down_left(gesture: Gesture) -> bool:
    return (
        gesture.direction.x > 0 and gesture.direction.y > 0 and matches_x_extrema(gesture, E.X_MIN) and matches_y_extrema(gesture, E.Y_MIN)
    )


def is_up_left(gesture: Gesture) -> bool:
    return (
        gesture.direction.x > 0 and gesture.direction.y < 0 and matches_x_extrema(gesture, E.X_MIN) and matches_y_extrema(gesture, E.Y_MAX)
    )


def is_up_down_curve(gesture: Gesture) -> bool:
    return is_turn_point_type(gesture.last_y_turn_point, TurnType.UP_TO_DOWN) and matches(gesture.iter_y_extrema(), E.Y_MAX, E.Y_MIN)


def is_down_up_curve(gesture: Gesture) -> bool:
    return is_turn_point_type(gesture.last_y_turn_point, TurnType.DOWN_TO_UP) and matches(gesture.iter_y_extrema(), E.Y_MIN, E.Y_MAX)


def is_left_right_curve(gesture: Gesture) -> bool:
    return is_turn_point_type(gesture.last_x_turn_point, TurnType.LEFT_TO_RIGHT) and matches(gesture.iter_x_extrema(), E.X_MIN, E.X_MAX)


def is_turn_point_type(turn_point: TurnPoint | None, turn_type: TurnType) -> bool:
    return turn_point is not None and turn_point.type == turn_type


def is_up(gesture: Gesture) -> bool:
    return gesture.direction.y < 0 and gesture.direction_abs.x < gesture.direction_abs.y and matches(gesture.iter_y_extrema(), E.Y_MAX)


def is_down(gesture: Gesture) -> bool:
    return gesture.direction.y > 0 and gesture.direction_abs.x < gesture.direction_abs.y and matches(gesture.iter_y_extrema(), E.Y_MIN)


def is_right(gesture: Gesture) -> bool:
    return gesture.direction.x < 0 and gesture.direction_abs.x > gesture.direction_abs.y and matches(gesture.iter_x_extrema(), E.X_MAX)


def is_left(gesture: Gesture) -> bool:
    return gesture.direction.x > 0 and gesture.direction_abs.x > gesture.direction_abs.y and matches(gesture.iter_x_extrema(), E.X_MIN)


def is_right_left_curve(gesture: Gesture) -> bool:
    return is_turn_point_type(gesture.last_x_turn_point, TurnType.RIGHT_TO_LEFT) and matches_x_extrema(gesture, E.X_MAX, E.X_MIN)


def matches_x_extrema(gesture: Gesture, *targets: E) -> bool:
    return matches_extrema(gesture.iter_x_extrema(), *targets)


def matches_y_extrema(gesture: Gesture, *targets: E) -> bool:
    return matches_extrema(gesture.iter_y_extrema(), *targets)


def matches_extrema(extrema: Iterable[E], *targets: E) -> bool:
    return matches(extrema, *targets)


def matches_x_turn_types(gesture: Gesture, *turn_types: TurnType) -> bool:
    return matches_turn_types(gesture.iter_x_turn_types(), *turn_types)

def matches_y_turn_types(gesture: Gesture, *turn_types: TurnType) -> bool:
    return matches_turn_types(gesture.iter_y_turn_types(), *turn_types)

def matches_turn_types(turn_types: Iterable[TurnType], *targets: TurnType) -> bool:
    return matches(turn_types, *targets)