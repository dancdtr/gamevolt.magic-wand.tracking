from gamevolt.configuration.appsetting import appsetting
from gamevolt.web_sockets.configuration.web_socket_server_settings import WebSocketServerSettings


@appsetting
class WandServerSettings:
    disconnect_after_s: float
    web_socket: WebSocketServerSettings
