from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from zones.visualisation.zone_presentation_controller import ZonePresentationController
from zones.visualisation.zone_visualiser_protocol import ZoneVisualiserProtocol
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZoneApplication:
    """Bundles a `ZoneManagerProtocol` with optional dev-only UI / visualiser.

    Production deployments pass `presentation_controller=None` and
    `controls=None` — they just want the manager, driven by real positioning
    input, with downstream consumers reacting to its events. Dev / mock
    deployments add zone controls (keyboard zone select) and a
    `ZonePresentationController` bound to the spell-target visualiser.
    Quit is propagated only by the presentation controller (visualiser
    window close), so controls without a visualiser cannot trigger quit.
    """

    def __init__(
        self,
        logger: Logger,
        zone_manager: ZoneManagerProtocol,
        presentation_controller: ZonePresentationController | None = None,
        controls: object | None = None,
    ) -> None:
        self.quit: Event[Callable[[], None]] = Event()

        self._presentation_controller = presentation_controller
        self._zone_manager = zone_manager
        self._controls = controls
        self._logger = logger

    @property
    def zone_manager(self) -> ZoneManagerProtocol:
        return self._zone_manager

    @property
    def zone_visualiser(self) -> ZoneVisualiserProtocol | None:
        """Dev-only spell-target visualiser; None in production."""
        if self._presentation_controller is None:
            return None
        return self._presentation_controller.visualiser

    async def start_async(self) -> None:
        await self._zone_manager.start_async()
        if self._presentation_controller is not None:
            await self._presentation_controller.start_async()
            self._presentation_controller.quit.subscribe(self._on_quit)

    async def stop_async(self) -> None:
        if self._presentation_controller is not None:
            self._presentation_controller.quit.unsubscribe(self._on_quit)
            await self._presentation_controller.stop_async()
        await self._zone_manager.stop_async()

    def update(self) -> None:
        if self._presentation_controller is not None:
            self._presentation_controller.update()

    def _on_quit(self) -> None:
        self._logger.info("ZoneApplication quit requested")
        self.quit.invoke()
