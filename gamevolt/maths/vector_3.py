from dataclasses import dataclass


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def __repr__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"

    def __format__(self, spec: str) -> str:
        signed_spec = "+" + spec
        return f"({format(self.x, signed_spec)}, " f"{format(self.y, signed_spec)}, " f"{format(self.z, signed_spec)})"
