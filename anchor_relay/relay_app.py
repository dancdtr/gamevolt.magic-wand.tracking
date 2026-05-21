from __future__ import annotations

from logging import Logger

from anchor_area.anchor_area_controller import AnchorAreaController
from anchor_relay.anchor_relay import AnchorRelay
from gamevolt.messaging.command_bridge.anchor_command_bridge import AnchorCommandBridge
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.web_sockets.web_socket_client import WebSocketClient


class RelayApp:
    def __init__(
        self,
        logger: Logger,
        web_socket_client: WebSocketClient,
        message_handler: MessageHandler,
        bridge: AnchorCommandBridge,
        anchor_area_controller: AnchorAreaController,
        anchor_relay: AnchorRelay,
    ) -> None:
        self._logger = logger
        self._web_socket_client = web_socket_client
        self._message_handler = message_handler
        self._bridge = bridge
        self._anchor_area_controller = anchor_area_controller
        self._anchor_relay = anchor_relay

    async def start_async(self) -> None:
        self._bridge.start()
        self._message_handler.start()
        await self._web_socket_client.start_async()
        await self._anchor_relay.start_async()
        self._anchor_area_controller.start()

    async def stop_async(self) -> None:
        self._anchor_area_controller.stop()
        await self._anchor_relay.stop_async()
        await self._web_socket_client.stop_async()
        self._message_handler.stop()
        self._bridge.stop()

    def update(self) -> None:
        self._anchor_relay.update()
