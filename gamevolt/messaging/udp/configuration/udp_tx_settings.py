from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class UdpTxSettings(SettingsBase):
    host: str
    port: int

    @property
    def address(self) -> tuple[str, int]:
        return (self.host, self.port)
