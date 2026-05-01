from dataclasses import dataclass, field

from gamevolt.configuration.settings_base import SettingsBase
from wand.configuration.pinned_zone_settings import PinnedZoneSettings


@dataclass
class TrackedWandsSettings(SettingsBase):
    ids: list[str]
    pinned_zones: list[PinnedZoneSettings] = field(default_factory=list)
