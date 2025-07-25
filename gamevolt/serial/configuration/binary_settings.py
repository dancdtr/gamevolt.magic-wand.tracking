import struct
from dataclasses import dataclass


@dataclass
class BinarySettings:
    packet_format: str

    @property
    def packet_size(self) -> int:
        return struct.calcsize(self.packet_format)
