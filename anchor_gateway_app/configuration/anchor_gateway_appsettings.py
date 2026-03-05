from dataclasses import dataclass

from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.web_sockets.configuration.web_socket_client_settings import WebSocketClientSettings
from gv_logging.configuration.logging_settings import LoggingSettings


@dataclass
class AnchorGatewayAppSettings(AppSettingsBase):
    name: str
    id: str
    version: str
    logging: LoggingSettings
    serial_receiver: SerialReceiverSettings
    web_socket_client: WebSocketClientSettings
