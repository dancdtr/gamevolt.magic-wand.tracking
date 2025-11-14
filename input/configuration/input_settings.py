from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from input.factories.configuration.input_type import InputType
from input.factories.mouse.configuration.mouse_settings import MouseSettings
from input.factories.wand.configuration.wand_settings import WandSettings


@dataclass
class InputSettings(SettingsBase):
    input_type: InputType
    mouse: MouseSettings
    wand: WandSettings
