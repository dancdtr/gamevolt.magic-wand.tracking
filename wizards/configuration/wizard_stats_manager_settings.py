from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WizardStatsManagerSettings(SettingsBase):
    intermediate_threshold: int
    advanced_threshold: int
