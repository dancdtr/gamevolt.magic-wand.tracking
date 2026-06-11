from gamevolt.configuration.appsetting import appsetting
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from wand.streaming.eliko.configuration.eliko_command_sink_settings import ElikoCommandSinkSettings
from wand.streaming.eliko.configuration.eliko_parsing_settings import ElikoParsingSettings


@appsetting
class ElikoSingleAnchorStreamSettings:
    serial: SerialReceiverSettings
    parsing: ElikoParsingSettings
    command_sink: ElikoCommandSinkSettings
    subscribe_flag: str = "P"
