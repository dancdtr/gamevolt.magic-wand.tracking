from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WizardSettings(SettingsBase):
    names: list[str]
