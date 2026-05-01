from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class PinnedZoneSettings(SettingsBase):
    zone_id: str
    wand_ids: list[str]
