# wand_yawpitch_rmf_interpreter.py
from __future__ import annotations

import math

from input.wand.interpreters.configuration.rmf_settings import ClipMode, RMFSettings
from input.wand_position import WandPosition
from maths.utils import cross, dot, norm, normalize, ortho_normalize, rotate_axis_angle, wrap_pi
from maths.vec3 import Vec3


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
        self._settings = settings

        # Frame
        self._f_prev: Vec3 | None = None
        self._r_prev: Vec3 | None = None
        self._v_prev: Vec3 | None = None

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
        u = normalize(self._settings.world_up)
        r0 = cross(u, f0)
        if norm(r0) < 1e-6:
            # If pointing near-up, seed r0 using a canonical axis (X) projected into plane ⟂ f0
            r0 = cross((1.0, 0.0, 0.0), f0)
            if norm(r0) < 1e-6:
                r0 = cross((0.0, 1.0, 0.0), f0)

        f0, r0, v0 = ortho_normalize(f0, r0)

        self._f_prev, self._r_prev, self._v_prev = f0, r0, v0
        self._f_lock, self._r_lock, self._v_lock = f0, r0, v0

    # ── main entry ──────────────────────────────────────────────────────────

    def on_sample(self, id: str, ts_ms: int, yaw_deg: float, pitch_deg: float) -> WandPosition:
        yaw = math.radians(yaw_deg) + self._yaw_offset
        pitch = math.radians(pitch_deg)

        # --- absolute, bounded normalisation to [-1, 1] using symmetric limits ---
        yaw_rel = wrap_pi(yaw)  # shortest-path yaw around ±π
        yaw_lim = max(1e-6, math.radians(self._settings.abs_yaw_limit_deg))
        pit_lim = max(1e-6, math.radians(self._settings.abs_pitch_limit_deg))

        nx_raw = yaw_rel / yaw_lim
        ny_raw = pitch / pit_lim

        if self._settings.abs_clip_mode is ClipMode.DISCARD and (abs(nx_raw) > 1.0 or abs(ny_raw) > 1.0):
            nx = ny = None
        else:
            nx = max(-1.0, min(1.0, nx_raw))
            ny = max(-1.0, min(1.0, ny_raw))

        # apply absolute preview inversions only (not delta inversions)
        if nx and self._settings.abs_invert_x:
            nx = -nx
        if ny and self._settings.abs_invert_y:
            ny = -ny

        f_now = normalize(self._forward_from_yawpitch(yaw, pitch))

        if self._f_prev is None:
            self.lock_frame_from_yawpitch(yaw_deg, pitch_deg)
            nx, ny = self._abs_norm_from_locked(f_now)
            return WandPosition(id, ts_ms, 0.0, 0.0, nx, ny)

        # --- minimal rotation f_prev -> f_now (unchanged) ---
        cross_product = cross(self._f_prev, f_now)
        s = norm(cross_product)
        c = max(-1.0, min(1.0, dot(self._f_prev, f_now)))
        angle = math.atan2(s, c)
        if angle < self._settings.tiny_angle or s < self._settings.tiny_angle:
            self._f_prev = f_now
            nx, ny = self._abs_norm_from_locked(f_now)
            return WandPosition(id, ts_ms, 0.0, 0.0, nx, ny)

        axis = (cross_product[0] / s, cross_product[1] / s, cross_product[2] / s)
        dtheta = (axis[0] * angle, axis[1] * angle, axis[2] * angle)

        # --- choose basis for delta projection ------------------------------
        # New behaviour: express the incremental rotation in the fixed
        # "gesture canvas" defined at reset (f_lock, r_lock, v_lock),
        # instead of the moving local frame.
        if hasattr(self, "_r_lock") and hasattr(self, "_v_lock") and self._r_lock is not None and self._v_lock is not None:
            basis_r = self._r_lock  # "up/down" axis in locked plane
            basis_v = self._v_lock  # "left/right" axis in locked plane
        else:
            # Fallback to previous behaviour if lock not initialised yet
            basis_r = self._r_prev
            basis_v = self._v_prev

        dx = dot(dtheta, basis_v)
        dy = dot(dtheta, basis_r)

        if abs(dx) < self._settings.deadzone_x:
            dx = 0.0
        if abs(dy) < self._settings.deadzone_y:
            dy = 0.0
        if self._settings.invert_x:
            dx = -dx
        if self._settings.invert_y:
            dy = -dy
        dx *= self._settings.gain_x
        dy *= self._settings.gain_y

        r_now = rotate_axis_angle(self._r_prev, axis, angle)
        v_now = rotate_axis_angle(self._v_prev, axis, angle)
        f_now, r_now, v_now = ortho_normalize(f_now, r_now)

        if self._settings.keep_absolute:
            self._x_abs += dx
            self._y_abs += dy

        self._f_prev, self._r_prev, self._v_prev = f_now, r_now, v_now
        nx, ny = self._abs_norm_from_locked(f_now)

        return WandPosition(id, ts_ms, dx, dy, nx, ny)

    # ── internals ───────────────────────────────────────────────────────────
    def _forward_from_yawpitch(self, yaw: float, pitch: float) -> Vec3:
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        # Standard "no-roll" forward for Z(yaw) then Y(pitch)
        return normalize((cp * cy, cp * sy, sp))

    def _abs_norm_from_locked(self, f_now: Vec3) -> tuple[float | None, float | None]:
        """
        Map minimal rotation f_lock -> f_now to view-plane components:
        ox = angle component about v_lock (left/right)
        oy = angle component about r_lock (up/down)
        Then normalise using cfg.abs_* limits to [-1,1].
        """
        if self._f_lock is None or self._r_lock is None or self._v_lock is None:
            return None, None

        cross_product = cross(self._f_lock, f_now)
        s = norm(cross_product)  # = sin(angle)
        c = max(-1.0, min(1.0, dot(self._f_lock, f_now)))  # = cos(angle)
        angle = math.atan2(s, c)  # ∈ [0, π]

        # Axis is ambiguous at 0 or 180°; choose a stable fallback (r_lock)
        if s < self._settings.tiny_angle:
            axis = self._r_lock
        else:
            axis = (cross_product[0] / s, cross_product[1] / s, cross_product[2] / s)

        # Rotation vector (Rodrigues parameters)
        omega = (axis[0] * angle, axis[1] * angle, axis[2] * angle)

        # Decompose onto locked view-plane axes
        ox = dot(omega, self._v_lock)  # left/right component (yawish)
        oy = dot(omega, self._r_lock)  # up/down component (pitchish)

        # Normalise with symmetric limits
        yaw_lim = max(1e-6, math.radians(self._settings.abs_yaw_limit_deg))
        pit_lim = max(1e-6, math.radians(self._settings.abs_pitch_limit_deg))
        nx_raw = ox / yaw_lim
        ny_raw = oy / pit_lim

        # Clip or discard
        if self._settings.abs_clip_mode is ClipMode.DISCARD and (abs(nx_raw) > 1.0 or abs(ny_raw) > 1.0):
            return None, None

        nx = max(-1.0, min(1.0, nx_raw))
        ny = max(-1.0, min(1.0, ny_raw))

        # Absolute (preview) inversion only
        if self._settings.abs_invert_x:
            nx = -nx
        if self._settings.abs_invert_y:
            ny = -ny
        return nx, ny
