from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class TcpClientSettings(SettingsBase):
    host: str
    port: int
    reconnect_delay_s: float
