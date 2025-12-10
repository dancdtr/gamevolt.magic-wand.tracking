from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, ClassVar, Iterable, Self

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.maths.axis import Axis
from maths.vec3 import Vec3


class ClipMode(Enum):
    NONE = auto()
    CLAMP = auto()
    DISCARD = auto()


class Axis3(Enum):
    X = auto()
    Y = auto()
    Z = auto()

    def get_vec3(self) -> Vec3:
        if self is Axis3.X:
            return (1, 0, 0)
        elif self is Axis3.Y:
            return (0, 1, 0)
        elif self is Axis3.Z:
            return (0, 0, 1)
        else:
            raise ValueError(f"No Vec3 defined for '{self}'.")


def _parse_world_up(x: Any) -> Vec3:
    # Allow "X"/"Y"/"Z", Axis3, or [x,y,z]
    if isinstance(x, str):
        return Axis3[x.strip().upper()].get_vec3()
    if isinstance(x, Axis3):
        return x.get_vec3()
    if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
        xs = list(x)
        if len(xs) != 3:
            raise ValueError(f"world_up must have 3 elements, got {x!r}")
        return (float(xs[0]), float(xs[1]), float(xs[2]))
    raise ValueError(f"Unsupported world_up value: {x!r}")


@dataclass
class RMFSettings(SettingsBase):
    world_up: Vec3 = (0.0, 0.0, 1.0)

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
    abs_clip_mode: ClipMode = ClipMode.CLAMP

    keep_absolute: bool = True
    tiny_angle: float = 1e-9

    FIELD_HANDLERS: ClassVar[dict[str, Any]] = {
        "tiny_angle": lambda x: float(x) if float(x) > 0.0 else 1e-9,
        "world_up": _parse_world_up,
    }
