from __future__ import annotations

import math

from wand.streaming.eliko_single_anchor.sflp_quat_stabiliser import SflpQuatStabiliser


def _forward(q: tuple[float, float, float, float]) -> tuple[float, float, float]:
    # Rotate body +Y by q (same algebra as quat_forward_encoder).
    qx, qy, qz, qw = q
    vx, vy, vz = 0.0, 1.0, 0.0
    tx = 2.0 * (qy * vz - qz * vy)
    ty = 2.0 * (qz * vx - qx * vz)
    tz = 2.0 * (qx * vy - qy * vx)
    f = (
        vx + qw * tx + (qy * tz - qz * ty),
        vy + qw * ty + (qz * tx - qx * tz),
        vz + qw * tz + (qx * ty - qy * tx),
    )
    m = math.sqrt(sum(c * c for c in f))
    return (f[0] / m, f[1] / m, f[2] / m)


def _angle_deg(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    d = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))
    return math.degrees(math.acos(d))


def _unit_quat(x: float, y: float, z: float, w: float) -> tuple[float, float, float, float]:
    m = math.sqrt(x * x + y * y + z * z + w * w)
    return (x / m, y / m, z / m, w / m)


def test_passthrough_outside_zone() -> None:
    stabiliser = SflpQuatStabiliser(zone=0.25)
    q = _unit_quat(0.1, 0.2, 0.3, 0.9)  # |w| well outside the zone
    assert stabiliser.refine(*q) == q


def test_suppresses_w_bounce_near_zero() -> None:
    """Emulate the captured failure: a stationary wand near w~0 whose recovered
    w bounces 0.00-0.05 from half-float quantisation. The stabilised forward
    must move far less than the raw one."""
    base = _unit_quat(0.70, -0.67, -0.21, 0.0)
    noisy_ws = [0.0, 0.049, 0.041, 0.032, 0.0, 0.043, 0.05, 0.038, 0.0, 0.045]

    def with_w(w: float) -> tuple[float, float, float, float]:
        s = math.sqrt(1.0 - w * w)
        return (base[0] * s, base[1] * s, base[2] * s, w)

    stabiliser = SflpQuatStabiliser()
    raw_max = 0.0
    refined_max = 0.0
    prev_raw = prev_refined = None
    for w in noisy_ws:
        q = with_w(w)
        refined = stabiliser.refine(*q)
        f_raw, f_ref = _forward(q), _forward(refined)
        if prev_raw is not None:
            raw_max = max(raw_max, _angle_deg(prev_raw, f_raw))
            refined_max = max(refined_max, _angle_deg(prev_refined, f_ref))
        prev_raw, prev_refined = f_raw, f_ref

    assert raw_max > 3.0  # the raw bounce is a real, visible spike
    assert refined_max < raw_max / 3.0


def test_refined_quat_stays_unit_norm() -> None:
    stabiliser = SflpQuatStabiliser()
    for w in (0.0, 0.02, 0.05, 0.1, 0.2):
        s = math.sqrt(1.0 - w * w)
        q = stabiliser.refine(0.7 * s / 0.7616, -0.3 * s / 0.7616, 0.0, w)
        norm = math.sqrt(sum(c * c for c in q))
        assert abs(norm - 1.0) < 1e-9


def test_hemisphere_flips_do_not_disturb_rotation() -> None:
    """The sensor alternates q / -q while hovering at the w~0 boundary; both
    represent the same rotation so the refined forward must stay put."""
    base = _unit_quat(0.70, -0.67, -0.21, 0.02)
    stabiliser = SflpQuatStabiliser()
    forwards = []
    for i in range(6):
        q = base if i % 2 == 0 else tuple(-c for c in base)
        forwards.append(_forward(stabiliser.refine(*q)))
    for a, b in zip(forwards, forwards[1:]):
        assert _angle_deg(a, b) < 0.01
