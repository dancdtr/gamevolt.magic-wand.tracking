from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from zones.mock_zone_controls import MockZoneControls
from zones.visualisation.zone_presentation_controller import ZonePresentationController
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZoneApplication:
    def __init__(
        self,
        logger: Logger,
        zone_manager: ZoneManagerProtocol,
        presentation_controller: ZonePresentationController,
        controls: MockZoneControls | None = None,
    ) -> None:
        self.quit: Event[Callable[[], None]] = Event()

        self._presentation_controller = presentation_controller
        self._zone_manager = zone_manager
        self._controls = controls
        self._logger = logger

    @property
    def zone_manager(self) -> ZoneManagerProtocol:
        return self._zone_manager

    async def start_async(self) -> None:
        await self._zone_manager.start_async()
        await self._presentation_controller.start_async()

        if self._controls is not None:
            if hasattr(self._controls, "quit"):
                self._controls.quit.subscribe(self._on_quit)
            if hasattr(self._controls, "start_async"):
                await self._controls.start_async()

        self._presentation_controller.quit.subscribe(self._on_quit)

    async def stop_async(self) -> None:
        self._presentation_controller.quit.unsubscribe(self._on_quit)

        if self._controls is not None:
            if hasattr(self._controls, "quit"):
                self._controls.quit.unsubscribe(self._on_quit)
            if hasattr(self._controls, "stop_async"):
                await self._controls.stop_async()

        await self._presentation_controller.stop_async()
        await self._zone_manager.stop_async()

    def update(self) -> None:
        self._presentation_controller.update()

    def _on_quit(self) -> None:
        self._logger.info("ZoneApplication quit requested")
        self.quit.invoke()
