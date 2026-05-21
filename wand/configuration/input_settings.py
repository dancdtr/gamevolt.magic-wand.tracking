from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from wand.configuration.tracked_wands_settings import TrackedWandsSettings
from wand.configuration.wand_settings import WandSettings


@dataclass
class InputSettings(SettingsBase):
    tracked_wands: TrackedWandsSettings
    wand: WandSettings
