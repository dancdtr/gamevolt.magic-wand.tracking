from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from gamevolt.web_sockets.web_socket_server import WebSocketServer


class WebSocketLineReceiver(LineReceiverProtocol):
    def __init__(self, logger: Logger, web_socket_server: WebSocketServer) -> None:
        self._line_received: Event[Callable[[str], None]] = Event()

        self._web_socket_server = web_socket_server
        self._logger = logger

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._line_received

    def start(self) -> None:
        self._web_socket_server.message_received.subscribe(self._on_line_received)

    def stop(self) -> None:
        self._web_socket_server.message_received.unsubscribe(self._on_line_received)

    def _on_line_received(self, line: str) -> None:
        self._line_received.invoke(line)
