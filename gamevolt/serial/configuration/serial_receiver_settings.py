from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class SerialReceiverSettings(SettingsBase):
    port: str
    baud: int
    timeout: int
    retry_interval: float
