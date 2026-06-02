from __future__ import annotations

_Q15_MAX = 32767


def quat_to_forward_q15(
    qx: float,
    qy: float,
    qz: float,
    qw: float,
    body_forward_x: float,
    body_forward_y: float,
    body_forward_z: float,
) -> tuple[int, int, int]:
    """Rotate body-frame forward vector by quaternion and Q15-encode the result.

    Algebra mirrors firmware `rotate_vec_by_quat` so results match the legacy
    path exactly when fed equivalent quats.
    """
    vx = body_forward_x
    vy = body_forward_y
    vz = body_forward_z

    tx = 2.0 * (qy * vz - qz * vy)
    ty = 2.0 * (qz * vx - qx * vz)
    tz = 2.0 * (qx * vy - qy * vx)

    fx = vx + qw * tx + (qy * tz - qz * ty)
    fy = vy + qw * ty + (qz * tx - qx * tz)
    fz = vz + qw * tz + (qx * ty - qy * tx)

    mag2 = fx * fx + fy * fy + fz * fz
    if mag2 > 1e-12:
        inv = mag2**-0.5
        fx *= inv
        fy *= inv
        fz *= inv

    return (_to_q15(fx), _to_q15(fy), _to_q15(fz))


def _to_q15(v: float) -> int:
    if v >= 1.0:
        return _Q15_MAX
    if v <= -1.0:
        return -_Q15_MAX
    return int(round(v * _Q15_MAX))
