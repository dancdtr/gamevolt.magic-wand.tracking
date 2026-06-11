from gamevolt.configuration.appsetting import appsetting
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.configuration.eliko_connection_settings import ElikoConnectionSettings
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings


@appsetting
class ElikoStreamSettings:
    connection: ElikoConnectionSettings
    parsing: ElikoParsingSettings
    command_sink: ElikoCommandSinkSettings
