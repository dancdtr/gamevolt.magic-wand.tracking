from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class AnchorAreaSettings(SettingsBase):
    id: str
    zone_ids: list[str]
