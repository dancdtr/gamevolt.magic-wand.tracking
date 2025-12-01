from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class UdpRxSettings(SettingsBase):
    host: str
    port: int
    max_size: int
    recv_timeout_s: float

    @property
    def address(self) -> tuple[str, int]:
        return (self.host, self.port)
