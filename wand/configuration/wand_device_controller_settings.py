from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WandDeviceControllerSettings(SettingsBase):
    spell_cast_pulse_colour: str
    spell_cast_pulse_period_ms: int
    spell_cast_pulse_duty_ms: int
    spell_cast_pulse_duration_s: float
