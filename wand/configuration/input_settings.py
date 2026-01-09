from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from wand.configuration.mock_wand_settings import MockWandSettings
from wand.configuration.tracked_wands_settings import TrackedWandsSettings
from wand.configuration.wand_server_settings import WandServerSettings
from wand.configuration.wand_settings import WandSettings
from wand.input_type import InputType


@dataclass
class InputSettings(SettingsBase):
    tracked_wands: TrackedWandsSettings
    server: WandServerSettings
    input_type: InputType
    mock: MockWandSettings
    wand: WandSettings
