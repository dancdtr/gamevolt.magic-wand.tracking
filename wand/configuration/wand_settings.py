from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from wand.interpreters.configuration.rmf_settings import RMFSettings


@dataclass
class WandSettings(SettingsBase):
    rmf: RMFSettings
