from __future__ import annotations

import random
import string
from bisect import bisect_left
from collections.abc import Iterator
from functools import cached_property

from detection.extremum_event import ExtremumEvent
from gamevolt.maths.extremum import Extremum
from gamevolt.maths.vector_2 import Vector2
from gestures.gesture_point import GesturePoint
from gestures.turn_event import TurnEvent
from gestures.turn_type import TurnType


class Gesture:
    def __init__(
        self,
        points: list[GesturePoint],
        duration: float,
        extrema_events: list[ExtremumEvent],
        turn_events: list[TurnEvent],
    ) -> None:
        self.points = points
        self.duration = duration
        self.turn_events = turn_events
        self.extrema_events = extrema_events

        self.direction = Vector2.from_average([p.velocity for p in points])

        self.id: int = random.randint(100000, 999999)

        self.total_velocity_n: float = 0
        self.total_velocity_e: float = 0
        self.total_velocity_s: float = 0
        self.total_velocity_w: float = 0

        for p in points:
            x, y = p.velocity
            if x >= 0:
                self.total_velocity_w += x
            else:
                self.total_velocity_e += abs(x)

            if y >= 0:
                self.total_velocity_s += y
            else:
                self.total_velocity_n += abs(y)

        def f(f: float) -> str:
            if f < 10:
                pad = "00"
            elif f < 100:
                pad = "0"
            else:
                pad = ""

            return f"{pad}{f:.2f}"

        print(
            f"({self.id})  N: {f(self.total_velocity_n)}  E: {f(self.total_velocity_e)} S: {f(self.total_velocity_s)} W: {f(self.total_velocity_w)}"
        )

    def iter_x_extrema(self) -> Iterator[Extremum]:
        return (e.type for e in self.extrema_events if e.type.is_x())

    def iter_y_extrema(self) -> Iterator[Extremum]:
        return (e.type for e in self.extrema_events if e.type.is_y())

    def iter_x_turn_points(self) -> Iterator[TurnType]:
        return (te.type for te in self.turn_events if te.type.in_x())

    def iter_y_turn_points(self) -> Iterator[TurnType]:
        return (te.type for te in self.turn_events if te.type.in_y())

    def iter_turn_types(self) -> Iterator[TurnType]:
        return (tp.type for tp in self.turn_events)

    def iter_x_turn_types(self) -> Iterator[TurnType]:
        return (tp.type for tp in self.turn_events if tp.type.in_x())

    def iter_y_turn_types(self) -> Iterator[TurnType]:
        return (tp.type for tp in self.turn_events if tp.type.in_y())

    # ---------- Lazy “last *” lookups ----------

    @property
    def first_turn_event(self) -> TurnEvent | None:
        return self.turn_events[0] if self.turn_events else None

    @property
    def first_x_turn_event(self) -> TurnEvent | None:
        for tp in self.turn_events:
            if tp.type.in_x():
                return tp
        return None

    @property
    def first_y_turn_event(self) -> TurnEvent | None:
        for tp in self.turn_events:
            if tp.type.in_y():
                return tp
        return None

    @property
    def last_turn_event(self) -> TurnEvent | None:
        return self.turn_events[-1] if self.turn_events else None

    @property
    def last_x_turn_event(self) -> TurnEvent | None:
        for tp in reversed(self.turn_events):
            if tp.type.in_x():
                return tp
        return None

    @property
    def last_y_turn_event(self) -> TurnEvent | None:
        for tp in reversed(self.turn_events):
            if tp.type.in_y():
                return tp
        return None

    @property
    def last_extremum_event(self) -> ExtremumEvent | None:
        # self.extrema_events[-1] if self.extrema_events else None
        if self.extrema_events:
            return self.extrema_events[-1]
        else:
            # print("no extrema events")
            return None

    # ---------- Direction helpers ----------

    @cached_property
    def direction_abs(self) -> Vector2:
        return Vector2(abs(self.direction.x), abs(self.direction.y))

    @property
    def min_direction_abs(self) -> float:
        d = self.direction_abs
        return d.x if d.x < d.y else d.y

    @property
    def max_direction_abs(self) -> float:
        d = self.direction_abs
        return d.x if d.x > d.y else d.y

    def split(self, normalised_time: float) -> tuple[Gesture, Gesture]:
        """
        Split by normalized time in (0,1).
        - Duplicates the boundary sample into both halves (interpolated if needed).
        - Duplicates events whose timestamp == split_ts into both halves.
        - Recomputes average_direction and duration for each half.
        """
        if not (0.0 < normalised_time < 1.0):
            raise ValueError("normalised_time must be in (0, 1)")
        if len(self.points) < 2:
            raise ValueError("Need at least two points to split")

        pts = self.points
        # assume points sorted by timestamp
        t0, t1 = pts[0].timestamp, pts[-1].timestamp
        span = t1 - t0
        if span <= 0:
            raise ValueError("Non-increasing timestamps; cannot split")

        # pick a split timestamp and clamp to interior so both sides are non-empty
        split_ts = t0 + int(round(normalised_time * span))
        if split_ts <= t0:
            split_ts = t0 + 1
        if split_ts >= t1:
            split_ts = t1 - 1

        # boundary point (exact or interpolated) — duplicate into both
        bpt = self._interp_point_at(pts, split_ts)
        # indices for slicing
        ts_list = [p.timestamp for p in pts]
        i = bisect_left(ts_list, split_ts)

        # left points: [t0, split) plus boundary
        left_points = pts[:i]
        if bpt is not None and (not left_points or left_points[-1].timestamp != bpt.timestamp):
            left_points = left_points + [bpt]

        # right points: [split, t1] plus boundary (at front)
        right_points = pts[i:]
        if bpt is not None:
            if not right_points or right_points[0].timestamp != bpt.timestamp:
                right_points = [bpt] + right_points

        # split events; duplicate those exactly on boundary
        def split_events_by_time[T](events: list[T], get_ts) -> tuple[list[T], list[T]]:
            left, right = [], []
            for ev in events:
                t = get_ts(ev)
                if t < split_ts:
                    left.append(ev)
                elif t > split_ts:
                    right.append(ev)
                else:
                    left.append(ev)
                    right.append(ev)
            return left, right

        left_ext, right_ext = split_events_by_time(self.extrema_events, lambda e: e.t_ms)
        left_turn, right_turn = split_events_by_time(self.turn_events, lambda e: e.t_ms)

        # recompute features per half
        def make(points: list[GesturePoint], extrema: list[ExtremumEvent], turns: list[TurnEvent]) -> Gesture:
            # avg = _avg_dir(points)
            avg = Vector2.from_average([p.velocity for p in points])
            dur = max(0.0, (points[-1].timestamp - points[0].timestamp) / 1000.0) if len(points) >= 2 else 0.0
            return Gesture(points, dur, extrema, turns)

        g_left = make(left_points, left_ext, left_turn)
        g_right = make(right_points, right_ext, right_turn)
        return (g_left, g_right)

    def _interp_point_at(self, points: list[GesturePoint], t_ms: int) -> GesturePoint | None:
        """Linear interpolation of velocity at t_ms; assumes points sorted by timestamp."""
        if not points:
            return None
        ts = [p.timestamp for p in points]
        i = bisect_left(ts, t_ms)
        if 0 <= i < len(points) and ts[i] == t_ms:
            return points[i]  # exact sample
        if 0 < i < len(points):
            a, b = points[i - 1], points[i]
            dt = max(1, b.timestamp - a.timestamp)
            w = (t_ms - a.timestamp) / dt
            vx = a.velocity.x + w * (b.velocity.x - a.velocity.x)
            vy = a.velocity.y + w * (b.velocity.y - a.velocity.y)
            return GesturePoint(Vector2(vx, vy), t_ms)
        return None  # outside range (shouldn’t happen if we clamp split_ts)
