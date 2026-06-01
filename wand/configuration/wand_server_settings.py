from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.web_sockets.configuration.web_socket_server_settings import WebSocketServerSettings


@dataclass
class WandServerSettings(SettingsBase):
    disconnect_after_s: float
    web_socket: WebSocketServerSettings
