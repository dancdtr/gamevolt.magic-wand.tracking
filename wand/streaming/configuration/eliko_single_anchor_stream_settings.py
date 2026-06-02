from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings


@dataclass
class ElikoSingleAnchorStreamSettings(SettingsBase):
    serial: SerialReceiverSettings
    parsing: ElikoParsingSettings
    command_sink: ElikoCommandSinkSettings
    subscribe_flag: str = "P"
