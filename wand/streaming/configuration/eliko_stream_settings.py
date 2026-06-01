from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.configuration.eliko_connection_settings import ElikoConnectionSettings
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings


@dataclass
class ElikoStreamSettings(SettingsBase):
    connection: ElikoConnectionSettings
    parsing: ElikoParsingSettings
    command_sink: ElikoCommandSinkSettings
