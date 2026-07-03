from __future__ import annotations

import math

Quat = tuple[float, float, float, float]


class SflpQuatStabiliser:
    """Suppresses the w-recovery noise inherent to the SFLP encoding.

    SFLP words carry only (x, y, z) of a unit quaternion as half-floats; w is
    recovered as sqrt(1 − x² − y² − z²). Near w ≈ 0 (wand ~180° from its
    IMU-init attitude) that square root is ill-conditioned: half-float
    quantisation of x/y/z makes the recovered w bounce by ~0.03-0.05 between
    samples, which swings the derived forward vector by several degrees —
    visible as trail jitter at specific orientations.

    Fix: track a sign-continuous w across samples (hemisphere-aligning each
    quat against the previous one), EMA-smooth it, and blend the smoothed w in
    only while |w| is inside the ill-conditioned zone. Outside the zone the
    quat passes through untouched, so responsiveness is unaffected at normal
    orientations. Measured on a captured jitter episode (2026-07-03 dump):
    worst per-sample forward swing 7.6° → 1.75°, with zero deviation added
    during fast genuine motion.

    Stateful per wand — one instance per tag, samples fed in stream order.
    """

    def __init__(self, zone: float = 0.25, smoothing_alpha: float = 0.12) -> None:
        self._zone = zone
        self._alpha = smoothing_alpha
        self._prev: Quat | None = None
        self._w_smoothed: float | None = None

    def reset(self) -> None:
        self._prev = None
        self._w_smoothed = None

    def refine(self, qx: float, qy: float, qz: float, qw: float) -> Quat:
        # Hemisphere-align against the previous sample so w is sign-continuous
        # (q and -q are the same rotation; the sensor emits w >= 0 only).
        if self._prev is not None:
            dot = qx * self._prev[0] + qy * self._prev[1] + qz * self._prev[2] + qw * self._prev[3]
            if dot < 0.0:
                qx, qy, qz, qw = -qx, -qy, -qz, -qw
        self._prev = (qx, qy, qz, qw)

        if self._w_smoothed is None:
            self._w_smoothed = qw
        else:
            self._w_smoothed += self._alpha * (qw - self._w_smoothed)

        # Blend fully at w=0, fading to passthrough at the zone edge.
        weight = 1.0 - abs(qw) / self._zone
        if weight <= 0.0:
            return (qx, qy, qz, qw)

        w = qw + weight * (self._w_smoothed - qw)
        w = max(-0.999, min(0.999, w))

        # Rescale xyz so the quat stays unit-norm with the corrected w.
        xyz_mag = math.sqrt(qx * qx + qy * qy + qz * qz)
        if xyz_mag < 1e-9:
            return (qx, qy, qz, qw)
        scale = math.sqrt(1.0 - w * w) / xyz_mag
        return (qx * scale, qy * scale, qz * scale, w)
