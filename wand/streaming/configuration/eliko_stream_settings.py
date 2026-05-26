from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class ElikoStreamSettings(SettingsBase):
    host: str
    port: int
    sample_dt_us: int
    reconnect_delay_s: float
