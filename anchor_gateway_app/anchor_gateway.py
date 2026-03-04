from logging import Logger

from gamevolt.serial.serial_receiver import SerialReceiver
from gamevolt.web_sockets.web_socket_client import WebSocketClient


class AnchorGateway:
    def __init__(self, logger: Logger, serial_receiver: SerialReceiver, websocket_client: WebSocketClient) -> None:
        self._serial_receiver = serial_receiver
        self._websocket = websocket_client
        self._logger = logger

    async def start_async(self) -> None:
        self._serial_receiver.line_received.subscribe(self._on_wand_rotation_raw)

        await self._serial_receiver.start()
        await self._websocket.start_async()

    async def stop_async(self) -> None:
        await self._websocket.stop_async()
        await self._serial_receiver.stop()

    def update(self) -> None:
        pass

    def _on_wand_rotation_raw(self, data: str) -> None:
        self._websocket.send_data(data)
