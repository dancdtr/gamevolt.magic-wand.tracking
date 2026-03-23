from dataclasses import dataclass

from gamevolt.configuration.settings_base import SettingsBase
from gamevolt.web_sockets.configuration.web_socket_server_settings import WebSocketServerSettings


@dataclass
class WandServerSettings(SettingsBase):
    header_ttl_s: float
    disconnect_after_s: float
    filter_wands: bool
    filtered_wand_ids: list[str]
    web_socket: WebSocketServerSettings
