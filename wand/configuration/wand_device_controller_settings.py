from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class WandDeviceControllerSettings(SettingsBase):
    command_broadcast_interval: float
    spell_under_cast_haptic_cues: list[int]
    wand_chosen_haptic_cues: list[int]
    spell_cast_haptic_cues: list[int]
    disable_wand_tx: bool
