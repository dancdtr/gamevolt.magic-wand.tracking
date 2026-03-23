from __future__ import annotations

import math

from maths.utils import cross, dot, norm, normalize
from maths.vec3 import Vec3
from wand.interpreters.configuration.rmf_settings import ClipMode, RMFSettings
from wand.wand_rotation import WandRotation


class ForwardGravityInterpreter:
    """
    Gravity-relative forward-vector interpreter.

    Input:
      - wand forward vector f = (fx, fy, fz), already in world frame
      - world up vector from config

    Output:
      - x_delta: signed azimuth-like change around world up
      - y_delta: signed elevation-like change relative to world up

    Sign convention:
      - x_delta > 0 : anticlockwise turn when viewed from above
      - y_delta > 0 : upward motion
    """

    def __init__(self, settings: RMFSettings = RMFSettings()) -> None:
        self._settings = settings

        self._u: Vec3 = normalize(self._settings.world_up)
        self._f_prev: Vec3 | None = None
        self._side_prev: Vec3 | None = None

        self._x_abs = 0.0
        self._y_abs = 0.0

        self._az_ref_x, self._az_ref_y = self._build_azimuth_basis()

    def reset(self) -> None:
        self._f_prev = None
        self._side_prev = None
        self._x_abs = 0.0
        self._y_abs = 0.0

    def on_sample(self, id: str, ts_ms: int, fx: float, fy: float, fz: float) -> WandRotation:
        f_now = normalize((fx, fy, fz))

        nx, ny = self._abs_norm_from_forward(f_now)

        if self._f_prev is None:
            self._f_prev = f_now
            self._side_prev = self._get_side_axis(f_now, None)
            return WandRotation(id, ts_ms, 0.0, 0.0, nx, ny)

        cross_product = cross(self._f_prev, f_now)
        s = norm(cross_product)
        c = max(-1.0, min(1.0, dot(self._f_prev, f_now)))
        angle = math.atan2(s, c)

        if angle < self._settings.tiny_angle or s < self._settings.tiny_angle:
            self._f_prev = f_now
            side_now = self._get_side_axis(f_now, self._side_prev)
            if side_now is not None:
                self._side_prev = side_now
            return WandRotation(id, ts_ms, 0.0, 0.0, nx, ny)

        axis = (cross_product[0] / s, cross_product[1] / s, cross_product[2] / s)
        omega = (axis[0] * angle, axis[1] * angle, axis[2] * angle)

        side_axis = self._get_side_axis(self._f_prev, self._side_prev)
        if side_axis is None:
            side_axis = (0.0, 0.0, 0.0)

        # Horizontal = turn around gravity axis
        dx = dot(omega, self._u)

        # Vertical = rotate around sideways axis
        dy = dot(omega, side_axis)

        # Near-vertical: horizontal direction becomes unreliable
        horiz_mag = norm(cross(self._u, self._f_prev))
        if horiz_mag < self._settings.tiny_angle:
            dx = 0.0

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

        if self._settings.keep_absolute:
            self._x_abs += dx
            self._y_abs += dy

        self._f_prev = f_now
        side_now = self._get_side_axis(f_now, self._side_prev)
        if side_now is not None:
            self._side_prev = side_now

        return WandRotation(id, ts_ms, dx, dy, nx, ny)

    def _build_azimuth_basis(self) -> tuple[Vec3, Vec3]:
        # Build a stable horizontal reference basis orthogonal to world up.
        candidate = (1.0, 0.0, 0.0)
        if abs(dot(candidate, self._u)) > 0.95:
            candidate = (0.0, 1.0, 0.0)

        x_ref = self._project_to_plane(candidate, self._u)
        x_ref = normalize(x_ref)
        y_ref = normalize(cross(self._u, x_ref))
        return x_ref, y_ref

    def _get_side_axis(self, f: Vec3, fallback: Vec3 | None) -> Vec3 | None:
        # Side axis used for elevation-ish movement.
        # Chosen so that upward motion gives positive dy.
        side = cross(f, self._u)
        side_mag = norm(side)

        if side_mag < self._settings.tiny_angle:
            return fallback

        return (side[0] / side_mag, side[1] / side_mag, side[2] / side_mag)

    def _project_to_plane(self, v: Vec3, n: Vec3) -> Vec3:
        d = dot(v, n)
        return (v[0] - d * n[0], v[1] - d * n[1], v[2] - d * n[2])

    def _abs_norm_from_forward(self, f_now: Vec3) -> tuple[float | None, float | None]:
        # Elevation from gravity
        elevation = math.asin(max(-1.0, min(1.0, dot(f_now, self._u))))

        # Azimuth around gravity using fixed global reference
        horiz = self._project_to_plane(f_now, self._u)
        horiz_mag = norm(horiz)

        if horiz_mag < self._settings.tiny_angle:
            azimuth = 0.0
        else:
            h = (horiz[0] / horiz_mag, horiz[1] / horiz_mag, horiz[2] / horiz_mag)
            azimuth = math.atan2(dot(h, self._az_ref_y), dot(h, self._az_ref_x))

        yaw_lim = max(1e-6, math.radians(self._settings.abs_yaw_limit_deg))
        pit_lim = max(1e-6, math.radians(self._settings.abs_pitch_limit_deg))

        nx_raw = azimuth / yaw_lim
        ny_raw = elevation / pit_lim

        if self._settings.abs_clip_mode is ClipMode.DISCARD and (abs(nx_raw) > 1.0 or abs(ny_raw) > 1.0):
            return None, None

        nx = max(-1.0, min(1.0, nx_raw))
        ny = max(-1.0, min(1.0, ny_raw))

        if self._settings.abs_invert_x:
            nx = -nx
        if self._settings.abs_invert_y:
            ny = -ny

        return nx, ny
