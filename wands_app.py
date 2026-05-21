from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from anchor_area.anchor_area_manager import AnchorAreaManager
from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.web_sockets.web_socket_server import WebSocketServer
from services.wand_session_coordinator import WandSessionCoordinator
from spell_cues.wand_spell_cue_controller import WandSpellCueController
from spells.spell_cast_presentation_controller import SpellCastPresentationController
from visualisation.visualiser_protocol import WandVisualiserProtocol
from wand.streaming.wand_sensor_stream import WandSensorStream
from wand.tracked_wand_manager import TrackedWandManager
from wand.wand_device_controller import WandDeviceController
from wand.wand_server import WandServer
from zones.zone_application import ZoneApplication


class WandsApp:
    def __init__(
        self,
        logger: Logger,
        web_socket_server: WebSocketServer,
        sensor_stream: WandSensorStream,
        server: WandServer,
        tracked_wand_manager: TrackedWandManager,
        wand_device_controller: WandDeviceController,
        wand_visualiser: WandVisualiserProtocol,
        zone_application: ZoneApplication,
        spell_cast_presentation_controller: SpellCastPresentationController,
        wand_session_coordinator: WandSessionCoordinator,
        anchor_area_manager: AnchorAreaManager,
        wand_spell_cue_controller: WandSpellCueController,
        zone_udp_receiver: UdpRx | None,
        zone_message_handler: MessageHandler | None,
    ) -> None:
        self.quit: Event[Callable[[], None]] = Event()

        self._logger = logger
        self._web_socket_server = web_socket_server
        self._sensor_stream = sensor_stream
        self._server = server
        self._tracked_wand_manager = tracked_wand_manager
        self._wand_device_controller = wand_device_controller
        self._wand_visualiser = wand_visualiser
        self._zone_application = zone_application
        self._spell_cast_presentation_controller = spell_cast_presentation_controller
        self._wand_session_coordinator = wand_session_coordinator
        self._anchor_area_manager = anchor_area_manager
        self._wand_spell_cue_controller = wand_spell_cue_controller
        self._zone_udp_receiver = zone_udp_receiver
        self._zone_message_handler = zone_message_handler

        self._tracked_wand_manager.wand_rotation_updated.subscribe(self._wand_visualiser.add_rotation)
        self._wand_visualiser.quit.subscribe(self._on_quit)
        self._zone_application.quit.subscribe(self._on_quit)

    async def start_async(self) -> None:
        if self._zone_udp_receiver is not None:
            await self._zone_udp_receiver.start_async()

        await self._web_socket_server.start_async()
        await self._zone_application.start_async()
        await self._spell_cast_presentation_controller.start_async()

        self._wand_session_coordinator.start()
        self._tracked_wand_manager.start()
        self._anchor_area_manager.start()

        if self._zone_message_handler is not None:
            self._zone_message_handler.start()

        self._wand_spell_cue_controller.start()
        await self._sensor_stream.start_async()
        self._server.start()
        self._wand_visualiser.start()

    async def stop_async(self) -> None:
        self._logger.info("Disabling all wands...")
        for wand in self._tracked_wand_manager.tracked_wands():
            self._wand_device_controller.blast_wand_inactive(wand.id)

        self._wand_visualiser.stop()
        self._server.stop()
        await self._sensor_stream.stop_async()
        self._wand_spell_cue_controller.stop()

        if self._zone_message_handler is not None:
            self._zone_message_handler.stop()

        self._anchor_area_manager.stop()
        self._tracked_wand_manager.stop()
        self._wand_session_coordinator.stop()

        await self._spell_cast_presentation_controller.stop_async()
        await self._zone_application.stop_async()
        await self._web_socket_server.stop_async()

        if self._zone_udp_receiver is not None:
            await self._zone_udp_receiver.stop_async()

        self._wand_visualiser.quit.unsubscribe(self._on_quit)
        self._zone_application.quit.unsubscribe(self._on_quit)
        self._tracked_wand_manager.wand_rotation_updated.unsubscribe(self._wand_visualiser.add_rotation)

    def update(self) -> None:
        self._sensor_stream.update()
        self._tracked_wand_manager.update()
        self._zone_application.update()
        self._wand_visualiser.update()

    def _on_quit(self) -> None:
        self._logger.info("WandsApp quit requested")
        self.quit.invoke()
