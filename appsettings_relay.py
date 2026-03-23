from dataclasses import dataclass

from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.logging.configuration.logging_settings import LoggingSettings
from gamevolt.messaging.command_bridge.configuration.anchor_command_bridge_settings import AnchorCommandBridgeSettings
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.web_sockets.configuration.web_socket_client_settings import WebSocketClientSettings


@dataclass
class AppSettingsRelay(AppSettingsBase):
    name: str
    id: str
    version: str
    logging: LoggingSettings
    serial_receiver: SerialReceiverSettings
    web_socket_client: WebSocketClientSettings
    anchor_command_bridge: AnchorCommandBridgeSettings
