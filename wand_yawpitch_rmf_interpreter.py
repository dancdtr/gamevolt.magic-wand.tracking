# wand_yawpitch_rmf_interpreter.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from gamevolt.events.event import Event
from input.wand_position import WandPosition


def _wrap_pi(rad: float) -> float:
    """Wrap any angle to [-pi, +pi)."""
    return ((rad + math.pi) % (2.0 * math.pi)) - math.pi


Vec3 = Tuple[float, float, float]


def _wrap180(deg: float) -> float:
    return ((deg + 180.0) % 360.0) - 180.0


def _clamp_unit(v: float) -> float:
    return -1.0 if v < -1.0 else (1.0 if v > 1.0 else v)


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
    up_world: Vec3 = (0.0, 0.0, 1.0)

    # Output shaping (deltas)
    gain_x: float = 1.0
    gain_y: float = 1.0
    deadzone_x: float = 0.0
    deadzone_y: float = 0.0
    invert_x: bool = False
    invert_y: bool = False

    # Absolute preview control (independent of delta invert)
    abs_invert_x: bool = False
    abs_invert_y: bool = False
    abs_yaw_limit_deg: float = 90.0  # map yaw ∈ [-limit, +limit] → [-1, +1]
    abs_pitch_limit_deg: float = 90.0  # map pitch ∈ [-limit, +limit] → [-1, +1]
    abs_clip_mode: str = "clamp"  # "clamp" | "discard"

    keep_absolute: bool = True
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

        # --- absolute, bounded normalisation to [-1, 1] using symmetric limits ---
        yaw_rel = _wrap_pi(yaw)  # shortest-path yaw around ±π
        yaw_lim = max(1e-6, math.radians(self.cfg.abs_yaw_limit_deg))
        pit_lim = max(1e-6, math.radians(self.cfg.abs_pitch_limit_deg))

        nx_raw = yaw_rel / yaw_lim
        ny_raw = pitch / pit_lim

        # if self.cfg.abs_clip_mode == "discard" and (abs(nx_raw) > 1.0 or abs(ny_raw) > 1.0):
        #     nx = ny = None
        # else:
        # clamp-to-range
        nx = max(-1.0, min(1.0, nx_raw))
        ny = max(-1.0, min(1.0, ny_raw))

        # apply absolute preview inversions only (not delta inversions)
        if self.cfg.abs_invert_x:
            nx = -nx
        if self.cfg.abs_invert_y:
            ny = -ny

        f_now = _normalize(self._forward_from_yawpitch(yaw, pitch))

        if self._f_prev is None:
            self.lock_frame_from_yawpitch(yaw_deg, pitch_deg)
            return WandPosition(ts_ms, 0.0, 0.0, nx, ny)

        # --- minimal rotation f_prev -> f_now (unchanged) ---
        cross = _cross(self._f_prev, f_now)
        s = _norm(cross)
        c = max(-1.0, min(1.0, _dot(self._f_prev, f_now)))
        angle = math.atan2(s, c)
        if angle < self.cfg.tiny_angle or s < self.cfg.tiny_angle:
            self._f_prev = f_now
            return WandPosition(ts_ms, 0.0, 0.0, nx, ny)

        axis = (cross[0] / s, cross[1] / s, cross[2] / s)
        dtheta = (axis[0] * angle, axis[1] * angle, axis[2] * angle)

        dx = _dot(dtheta, self._v_prev)
        dy = _dot(dtheta, self._r_prev)

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

        r_now = _rotate_axis_angle(self._r_prev, axis, angle)
        v_now = _rotate_axis_angle(self._v_prev, axis, angle)
        f_now, r_now, v_now = _orthonormalize(f_now, r_now)

        if self.cfg.keep_absolute:
            self._x_abs += dx
            self._y_abs += dy

        self._f_prev, self._r_prev, self._v_prev = f_now, r_now, v_now
        return WandPosition(ts_ms, dx, dy, nx, ny)

    # ── internals ───────────────────────────────────────────────────────────
    def _forward_from_yawpitch(self, yaw: float, pitch: float) -> Vec3:
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        # Standard "no-roll" forward for Z(yaw) then Y(pitch)
        return _normalize((cp * cy, cp * sy, sp))
