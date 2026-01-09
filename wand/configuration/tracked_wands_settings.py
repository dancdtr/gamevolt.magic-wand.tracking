from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class TrackedWandsSettings(SettingsBase):
    enable_filtering: bool
    filtered_ids: list[str]
