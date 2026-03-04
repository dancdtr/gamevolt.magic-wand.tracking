from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WandClientSettings(SettingsBase):
    imu_hz: float
    target_hz: float


@dataclass
class WandServerSettings(SettingsBase):
    header_ttl_s: float
    disconnect_after_s: float
    client: WandClientSettings
    filter_wands: bool
    filtered_wand_ids: list[str]
