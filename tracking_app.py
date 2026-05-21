from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from anchor_area.anchor_area_manager import AnchorAreaManager
from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.web_sockets.web_socket_server import WebSocketServer
from services.wand_session_coordinator import WandSessionCoordinator
from wand.streaming.wand_sensor_stream import WandSensorStream
from zones.zone_application import ZoneApplication


class TrackingApp:
    """Owns relay ingress, zone management, anchor-area mapping, and
    presence orchestration. Produces the sensor stream and presence
    events consumed by the RecognitionApp."""

    def __init__(
        self,
        logger: Logger,
        web_socket_server: WebSocketServer,
        sensor_stream: WandSensorStream,
        zone_application: ZoneApplication,
        anchor_area_manager: AnchorAreaManager,
        wand_session_coordinator: WandSessionCoordinator,
        zone_udp_receiver: UdpRx | None,
        zone_message_handler: MessageHandler | None,
    ) -> None:
        self.quit: Event[Callable[[], None]] = Event()

        self._logger = logger
        self._web_socket_server = web_socket_server
        self._sensor_stream = sensor_stream
        self._zone_application = zone_application
        self._anchor_area_manager = anchor_area_manager
        self._wand_session_coordinator = wand_session_coordinator
        self._zone_udp_receiver = zone_udp_receiver
        self._zone_message_handler = zone_message_handler

        self._zone_application.quit.subscribe(self._on_quit)

    async def start_async(self) -> None:
        if self._zone_udp_receiver is not None:
            await self._zone_udp_receiver.start_async()

        await self._web_socket_server.start_async()
        await self._zone_application.start_async()

        self._wand_session_coordinator.start()
        self._anchor_area_manager.start()

        if self._zone_message_handler is not None:
            self._zone_message_handler.start()

        await self._sensor_stream.start_async()

    async def stop_async(self) -> None:
        await self._sensor_stream.stop_async()

        if self._zone_message_handler is not None:
            self._zone_message_handler.stop()

        self._anchor_area_manager.stop()
        self._wand_session_coordinator.stop()

        await self._zone_application.stop_async()
        await self._web_socket_server.stop_async()

        if self._zone_udp_receiver is not None:
            await self._zone_udp_receiver.stop_async()

        self._zone_application.quit.unsubscribe(self._on_quit)

    def update(self) -> None:
        self._sensor_stream.update()
        self._zone_application.update()

    def _on_quit(self) -> None:
        self._logger.info("TrackingApp quit requested")
        self.quit.invoke()
