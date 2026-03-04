from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.web_sockets.configuration.web_socket_settings import WebSocketSettings


@dataclass
class WebSocketClientSettings(SettingsBase):
    web_socket: WebSocketSettings
    reconnection_interval: int
    timeout: float
