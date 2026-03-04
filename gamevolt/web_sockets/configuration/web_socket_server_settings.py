from dataclasses import dataclass

from attr import field

from game_volt.configuration.settings_base import SettingsBase
from game_volt.web_sockets.configuration.web_socket_settings import WebSocketSettings


@dataclass
class WebSocketServerSettings(SettingsBase):
    web_socket: WebSocketSettings
    select_interval: float = field(default=0.1)
