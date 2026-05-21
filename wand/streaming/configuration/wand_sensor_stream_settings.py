from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WandSensorStreamSettings(SettingsBase):
    header_ttl_s: float
