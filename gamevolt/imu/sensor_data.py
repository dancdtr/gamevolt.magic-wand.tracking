from dataclasses import dataclass

from vector_3 import Vector3


@dataclass
class SensorData:
    timestamp_ms: int
    accel: Vector3
    gyro: Vector3
    mag: Vector3

    def __repr__(self) -> str:
        return f"ts={self.timestamp_ms} | a={self.accel:.3f} | g={self.gyro:.3f} | m={self.mag:.3f}"
