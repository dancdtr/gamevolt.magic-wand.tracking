from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WandDeviceControllerSettings(SettingsBase):
    spell_cast_pulse_colour: str
    spell_cast_pulse_step: int
    rudimentary_spell_cast_pulse_duration_s: float
    skilled_spell_cast_pulse_duration_s: float
    experienced_spell_cast_pulse_duration_s: float
    mastered_spell_cast_pulse_duration_s: float
