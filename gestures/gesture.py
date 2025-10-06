from __future__ import annotations

import json
from bisect import bisect_left
from collections.abc import Iterator
from functools import cached_property
from typing import Counter

from numpy import hypot

from detection.extremum_event import ExtremumEvent
from gamevolt.maths.extremum import Extremum
from gamevolt.maths.vector_2 import Vector2
from gestures.gesture_point import GesturePoint
from gestures.turn_event import TurnEvent
from gestures.turn_type import TurnType


class Gesture:
    def __init__(
        self,
        id: str,
        points: list[GesturePoint],
        duration: float,
        extrema_events: list[ExtremumEvent],
        turn_events: list[TurnEvent],
    ) -> None:
        self.id = id
        self.points = points
        self.duration = duration
        self.turn_events = turn_events
        self.extrema_events = extrema_events

        self.direction = Vector2.from_average([p.velocity for p in points])

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

    def iter_x_extrema(self) -> Iterator[Extremum]:
        return (e.type for e in self.extrema_events if e.type.is_x())

    def iter_y_extrema(self) -> Iterator[Extremum]:
        return (e.type for e in self.extrema_events if e.type.is_y())

    def iter_x_turn_points(self) -> Iterator[TurnType]:
        return (te.turn_type for te in self.turn_events if te.turn_type.in_x())

    def iter_y_turn_points(self) -> Iterator[TurnType]:
        return (te.turn_type for te in self.turn_events if te.turn_type.in_y())

    def iter_turn_types(self) -> Iterator[TurnType]:
        return (tp.turn_type for tp in self.turn_events)

    def iter_x_turn_types(self) -> Iterator[TurnType]:
        return (tp.turn_type for tp in self.turn_events if tp.turn_type.in_x())

    def iter_y_turn_types(self) -> Iterator[TurnType]:
        return (tp.turn_type for tp in self.turn_events if tp.turn_type.in_y())

    # ---------- Lazy “last *” lookups ----------

    @property
    def first_turn_event(self) -> TurnEvent | None:
        return self.turn_events[0] if self.turn_events else None

    @property
    def first_x_turn_event(self) -> TurnEvent | None:
        for tp in self.turn_events:
            if tp.turn_type.in_x():
                return tp
        return None

    @property
    def first_y_turn_event(self) -> TurnEvent | None:
        for tp in self.turn_events:
            if tp.turn_type.in_y():
                return tp
        return None

    @property
    def last_turn_event(self) -> TurnEvent | None:
        return self.turn_events[-1] if self.turn_events else None

    @property
    def last_x_turn_event(self) -> TurnEvent | None:
        for tp in reversed(self.turn_events):
            if tp.turn_type.in_x():
                return tp
        return None

    @property
    def last_y_turn_event(self) -> TurnEvent | None:
        for tp in reversed(self.turn_events):
            if tp.turn_type.in_y():
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
            # avg = Vector2.from_average([p.velocity for p in points])
            dur = max(0.0, (points[-1].timestamp - points[0].timestamp) / 1000.0) if len(points) >= 2 else 0.0
            return Gesture(self.id, points, dur, extrema, turns)

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

    def __str__(self) -> str:
        # helpers
        def r(x: float | None, p: int = 4) -> float | None:
            return None if x is None else round(float(x), p)

        pts = self.points or []
        n = len(pts)
        t0 = pts[0].timestamp if n else None
        t1 = pts[-1].timestamp if n else None

        # basic stats over velocity
        if n:
            speeds = [hypot(p.velocity.x, p.velocity.y) for p in pts]
            avg_speed = sum(speeds) / n
            max_speed = max(speeds)
            avg_vx = sum(p.velocity.x for p in pts) / n
            avg_vy = sum(p.velocity.y for p in pts) / n
            min_vx = min(p.velocity.x for p in pts)
            max_vx = max(p.velocity.x for p in pts)
            min_vy = min(p.velocity.y for p in pts)
            max_vy = max(p.velocity.y for p in pts)
        else:
            speeds = []
            avg_speed = max_speed = avg_vx = avg_vy = min_vx = max_vx = min_vy = max_vy = 0.0

        # net direction (TODO: fix W/E, S/N, currently inverted for current IMU mounting)
        net_vx = sum(p.velocity.x for p in pts) if n else 0.0
        net_vy = sum(p.velocity.y for p in pts) if n else 0.0
        dom_axis = "X" if abs(net_vx) >= abs(net_vy) else "Y"
        dom_dir = ("W" if net_vx >= 0 else "E") if dom_axis == "X" else ("S" if net_vy >= 0 else "N")

        # turn & extremum sequences/counters
        turn_seq = [te.turn_type.name for te in self.turn_events]
        turn_times = [te.t_ms for te in self.turn_events]
        turn_counts = Counter(turn_seq)
        x_turn_seq = [te.turn_type.name for te in self.turn_events if te.turn_type.in_x()]
        y_turn_seq = [te.turn_type.name for te in self.turn_events if te.turn_type.in_y()]

        ext_seq = [e.type.name for e in self.extrema_events]
        ext_times = [e.t_ms for e in self.extrema_events]

        # compact per-point series: [t, vx, vy]
        # TODO temp - consolidate with other gesture points limit
        MAX_POINTS = 256
        trimmed = n > MAX_POINTS
        series = (
            [[pts[i].timestamp, r(pts[i].velocity.x), r(pts[i].velocity.y)] for i in range(n if not trimmed else MAX_POINTS)] if n else []
        )

        payload = {
            "id": self.id,
            "n_points": n,
            "t_start_ms": t0,
            "t_end_ms": t1,
            "duration_s": r(self.duration, 4),
            # direction (from precomputed average)
            "dir_avg": {"x": r(self.direction.x), "y": r(self.direction.y)},
            "dir_abs": {"x": r(self.direction_abs.x), "y": r(self.direction_abs.y)},
            "dir_dom_axis": dom_axis,
            "dir_dom_dir": dom_dir,  # "W"|"E" or "S"|"N" per your convention
            # velocity totals in current coordinate semantics
            "totals": {
                "N": r(self.total_velocity_n),
                "E": r(self.total_velocity_e),
                "S": r(self.total_velocity_s),
                "W": r(self.total_velocity_w),
                "net_vx": r(net_vx),
                "net_vy": r(net_vy),
            },
            # velocity stats
            "v_stats": {
                "avg_speed": r(avg_speed),
                "max_speed": r(max_speed),
                "avg_vx": r(avg_vx),
                "avg_vy": r(avg_vy),
                "min_vx": r(min_vx),
                "max_vx": r(max_vx),
                "min_vy": r(min_vy),
                "max_vy": r(max_vy),
            },
            # events (sequences + timestamps + counts)
            "turns": {
                "count": len(self.turn_events),
                "sequence": turn_seq,
                "timestamps_ms": turn_times,
                "counts_by_type": dict(turn_counts),
                "x_sequence": x_turn_seq,
                "y_sequence": y_turn_seq,
                "first": (self.first_turn_event.turn_type.name if self.first_turn_event else None),
                "last": (self.last_turn_event.turn_type.name if self.last_turn_event else None),
            },
            "extrema": {
                "count": len(self.extrema_events),
                "sequence": ext_seq,
                "timestamps_ms": ext_times,
                "last": (self.last_extremum_event.type.name if self.last_extremum_event else None),
            },
            # per-point series
            "series_v": {
                "cols": ["t_ms", "vx", "vy"],
                "trimmed": trimmed,
                "rows": series,
            },
        }

        # return compact JSON (TODO is key order stable? will it help diffing?)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)
