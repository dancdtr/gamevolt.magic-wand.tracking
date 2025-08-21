from dataclasses import dataclass


@dataclass
class ImuSettings:
    flip_x: bool
    flip_y: bool
    flip_z: bool
