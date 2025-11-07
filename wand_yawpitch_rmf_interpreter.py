# wand_yawpitch_rmf_interpreter.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from gamevolt.events.event import Event
from input.wand_position import WandPosition

Vec3 = Tuple[float, float, float]


# ── vector helpers ──────────────────────────────────────────────────────────
def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v: Vec3) -> float:
    return math.sqrt(_dot(v, v))


def _normalize(v: Vec3) -> Vec3:
    n = _norm(v)
    return (0.0, 0.0, 0.0) if n == 0.0 else (v[0] / n, v[1] / n, v[2] / n)


def _rotate_axis_angle(v: Vec3, axis: Vec3, angle: float) -> Vec3:
    """Rodrigues' rotation formula: rotate vector v around unit axis by angle."""
    a = _normalize(axis)
    c, s = math.cos(angle), math.sin(angle)
    dv = _dot(a, v)
    axv = _cross(a, v)
    return (
        v[0] * c + axv[0] * s + a[0] * dv * (1.0 - c),
        v[1] * c + axv[1] * s + a[1] * dv * (1.0 - c),
        v[2] * c + axv[2] * s + a[2] * dv * (1.0 - c),
    )


def _orthonormalize(f: Vec3, r: Vec3) -> Tuple[Vec3, Vec3, Vec3]:
    """Gram–Schmidt: make r ⟂ f; recompute v = f × r."""
    f = _normalize(f)
    r = (r[0] - f[0] * _dot(f, r), r[1] - f[1] * _dot(f, r), r[2] - f[2] * _dot(f, r))
    r = _normalize(r) if _norm(r) > 0 else (0.0, 0.0, 0.0)
    v = _cross(f, r)
    return f, r, v


# ── settings ────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class RMFSettings:
    # World up only used for initial seeding if you choose to seed from up; transport then avoids pole flips.
    up_world: Vec3 = (0.0, 0.0, 1.0)

    # Output shaping
    gain_x: float = 1.0
    gain_y: float = 1.0
    deadzone_x: float = 0.0
    deadzone_y: float = 0.0
    invert_x: bool = False
    invert_y: bool = False
    keep_absolute: bool = True

    # Numerical tolerances
    tiny_angle: float = 1e-9


# ── interpreter ─────────────────────────────────────────────────────────────
class YawPitchRMFInterpreter:
    """
    Rotation-Minimizing Frame (parallel transport) from yaw/pitch (no roll required).

    State: an orthonormal frame (f,r,v). At reset, we lock it.
    For each new sample:
      • Build forward f_now from yaw/pitch (+ optional heading offset if you add it).
      • Compute minimal rotation mapping f_prev → f_now:
          axis = normalize(f_prev × f_now)
          angle = atan2(|axis×|, dot(f_prev, f_now))
      • dθ = axis * angle  (small rotation vector in world)
      • Transport: r_prev, v_prev are rotated by the SAME (axis,angle) to get r_now, v_now.
        (This is the parallel transport — no flips at poles.)
      • Project:
          Δx = dot(dθ, v_prev)   # left/right in the view plane (previous frame)
          Δy = dot(dθ, r_prev)   # up/down   in the view plane (previous frame)
    """

    def __init__(self, settings: RMFSettings = RMFSettings()):
        self.cfg = settings

        # Frame
        self._f_prev: Optional[Vec3] = None
        self._r_prev: Optional[Vec3] = None
        self._v_prev: Optional[Vec3] = None

        # Absolute accumulators (optional)
        self._x_abs = 0.0
        self._y_abs = 0.0

        # Heading offset (optional; set to 0 unless you want a “rotate to +X” zero)
        self._yaw_offset = 0.0

    # ── public controls ─────────────────────────────────────────────────────
    def reset(self) -> None:
        """Clear frame & accumulators. Call lock_frame_* again to re-seed."""
        self._f_prev = self._r_prev = self._v_prev = None
        self._x_abs = self._y_abs = 0.0
        self._yaw_offset = 0.0

    def zero_absolute(self) -> None:
        self._x_abs = self._y_abs = 0.0

    def set_heading_offset_rad(self, yaw_rad: float) -> None:
        """Optional: static yaw offset (about world up) applied when building forward."""
        self._yaw_offset = yaw_rad

    def lock_frame_from_yawpitch(self, yaw_deg: float, pitch_deg: float) -> None:
        """
        Define and lock the initial frame from current yaw/pitch.
        r is seeded from world up to give an intuitive side (then transport keeps it stable).
        """
        yaw = math.radians(yaw_deg) + self._yaw_offset
        pitch = math.radians(pitch_deg)
        f0 = self._forward_from_yawpitch(yaw, pitch)

        # Seed r0 using up_world, fallback if nearly parallel
        u = _normalize(self.cfg.up_world)
        r0 = _cross(u, f0)
        if _norm(r0) < 1e-6:
            # If pointing near-up, seed r0 using a canonical axis (X) projected into plane ⟂ f0
            r0 = _cross((1.0, 0.0, 0.0), f0)
            if _norm(r0) < 1e-6:
                r0 = _cross((0.0, 1.0, 0.0), f0)

        f0, r0, v0 = _orthonormalize(f0, r0)

        self._f_prev = f0
        self._r_prev = r0
        self._v_prev = v0

    # ── main entry ──────────────────────────────────────────────────────────
    def on_sample(self, ts_ms: int, yaw_deg: float, pitch_deg: float) -> WandPosition:
        yaw = math.radians(yaw_deg) + self._yaw_offset
        pitch = math.radians(pitch_deg)
        f_now = _normalize(self._forward_from_yawpitch(yaw, pitch))

        if self._f_prev is None:
            # If user forgot to call lock_frame*, seed from this sample
            self.lock_frame_from_yawpitch(yaw_deg, pitch_deg)
            return WandPosition(ts_ms, 0.0, 0.0)

        # Minimal rotation f_prev -> f_now
        cross = _cross(self._f_prev, f_now)
        s = _norm(cross)  # = sin(angle)
        c = max(-1.0, min(1.0, _dot(self._f_prev, f_now)))  # = cos(angle)
        angle = math.atan2(s, c)
        if angle < self.cfg.tiny_angle or s < self.cfg.tiny_angle:
            # Tiny motion: keep frame, emit ~0
            self._f_prev = f_now
            return WandPosition(ts_ms, 0.0, 0.0)
        axis = (cross[0] / s, cross[1] / s, cross[2] / s)
        dtheta = (axis[0] * angle, axis[1] * angle, axis[2] * angle)

        # Project deltas on the PREVIOUS transported view-plane axes
        # (using previous keeps signs consistent and avoids instantaneous flips)
        dx = _dot(dtheta, self._v_prev)  # left/right
        dy = _dot(dtheta, self._r_prev)  # up/down

        # Conditioning
        if abs(dx) < self.cfg.deadzone_x:
            dx = 0.0
        if abs(dy) < self.cfg.deadzone_y:
            dy = 0.0
        if self.cfg.invert_x:
            dx = -dx
        if self.cfg.invert_y:
            dy = -dy
        dx *= self.cfg.gain_x
        dy *= self.cfg.gain_y

        # Transport the frame by the SAME minimal rotation
        r_now = _rotate_axis_angle(self._r_prev, axis, angle)
        v_now = _rotate_axis_angle(self._v_prev, axis, angle)
        # Re-orthonormalize (numerical hygiene)
        f_now, r_now, v_now = _orthonormalize(f_now, r_now)

        # Integrate absolute if desired
        x_abs = y_abs = None
        if self.cfg.keep_absolute:
            self._x_abs += dx
            self._y_abs += dy
            x_abs, y_abs = self._x_abs, self._y_abs

        # Emit and update state
        self._f_prev, self._r_prev, self._v_prev = f_now, r_now, v_now
        return WandPosition(ts_ms, dx, dy, x_abs, y_abs)

    # ── internals ───────────────────────────────────────────────────────────
    def _forward_from_yawpitch(self, yaw: float, pitch: float) -> Vec3:
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        # Standard "no-roll" forward for Z(yaw) then Y(pitch)
        return _normalize((cp * cy, cp * sy, sp))

    # def _emit(self, ts_ms: int, dx: float, dy: float, x: Optional[float] = None, y: Optional[float] = None) -> None:
    # self.position_updated.invoke(WandPosition(ts_ms=ts_ms, x_delta=dx, y_delta=dy, x=x, y=y))
