from dataclasses import dataclass


@dataclass
class UdpTxSettings:
    host: str
    port: int

    @property
    def address(self) -> tuple[str, int]:
        return (self.host, self.port)
