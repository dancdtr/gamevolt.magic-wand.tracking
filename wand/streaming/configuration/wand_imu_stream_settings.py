from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WandImuStreamSettings(SettingsBase):
    header_ttl_s: float
