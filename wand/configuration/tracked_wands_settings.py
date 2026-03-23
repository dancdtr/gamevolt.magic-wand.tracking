from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class TrackedWandsSettings(SettingsBase):
    ids: list[str]
