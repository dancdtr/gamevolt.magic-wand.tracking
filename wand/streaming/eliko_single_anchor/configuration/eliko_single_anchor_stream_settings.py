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
    # When False the app issues no IMU-enable traffic (init CMD0s + post-reboot
    # re-enable) and no reboot detector is wired. Use when another system (e.g.
    # the RTLS network) owns wand IMU state.
    manage_imu: bool = True
