from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class ElikoParsingSettings(SettingsBase):
    sample_dt_us: int
    nsamp_per_packet: int
    body_forward_x: float
    body_forward_y: float
    body_forward_z: float
