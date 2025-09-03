from dataclasses import dataclass


@dataclass
class UdpRxSettings:
    host: str
    port: int
    max_size: int
    recv_timeout_s: float

    @property
    def address(self) -> tuple[str, int]:
        return (self.host, self.port)
