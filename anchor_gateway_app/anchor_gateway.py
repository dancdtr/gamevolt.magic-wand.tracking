from logging import Logger

from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from gamevolt.web_sockets.web_socket_client import WebSocketClient


class AnchorGateway:
    def __init__(self, logger: Logger, line_receiver_protocol: LineReceiverProtocol, web_socket_client: WebSocketClient) -> None:
        self._line_receiver_protocol = line_receiver_protocol
        self._web_socket_client = web_socket_client
        self._logger = logger

    async def start_async(self) -> None:
        self._line_receiver_protocol.line_received.subscribe(self._on_line_received)

        await self._line_receiver_protocol.start_async()
        await self._web_socket_client.start_async()

    async def stop_async(self) -> None:
        await self._web_socket_client.stop_async()
        await self._line_receiver_protocol.stop_async()

        self._line_receiver_protocol.line_received.unsubscribe(self._on_line_received)

    def update(self) -> None:
        pass

    def _on_line_received(self, raw: str) -> None:
        self._web_socket_client.send_data(raw)
