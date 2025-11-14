import math

from maths.vec3 import Vec3


def wrap_pi(rad: float) -> float:
    """Wrap any angle to [-pi, +pi)."""
    return ((rad + math.pi) % (2.0 * math.pi)) - math.pi


def _wrap180(deg: float) -> float:
    return ((deg + 180.0) % 360.0) - 180.0


def _clamp_unit(v: float) -> float:
    return -1.0 if v < -1.0 else (1.0 if v > 1.0 else v)


def dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(v: Vec3) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: Vec3) -> Vec3:
    n = norm(v)
    return (0.0, 0.0, 0.0) if n == 0.0 else (v[0] / n, v[1] / n, v[2] / n)


def rotate_axis_angle(v: Vec3, axis: Vec3, angle: float) -> Vec3:
    """Rodrigues' rotation formula: rotate vector v around unit axis by angle."""
    a = normalize(axis)
    c, s = math.cos(angle), math.sin(angle)
    dv = dot(a, v)
    axv = cross(a, v)
    return (
        v[0] * c + axv[0] * s + a[0] * dv * (1.0 - c),
        v[1] * c + axv[1] * s + a[1] * dv * (1.0 - c),
        v[2] * c + axv[2] * s + a[2] * dv * (1.0 - c),
    )


def ortho_normalize(f: Vec3, r: Vec3) -> tuple[Vec3, Vec3, Vec3]:
    """Gram-Schmidt: make r ⟂ f; recompute v = f x r."""
    f = normalize(f)
    r = (r[0] - f[0] * dot(f, r), r[1] - f[1] * dot(f, r), r[2] - f[2] * dot(f, r))
    r = normalize(r) if norm(r) > 0 else (0.0, 0.0, 0.0)
    v = cross(f, r)
    return f, r, v
