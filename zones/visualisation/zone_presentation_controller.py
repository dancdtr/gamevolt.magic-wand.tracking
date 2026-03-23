from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from zones.visualisation.zone_visualiser_protocol import ZoneVisualiserProtocol
from zones.zone import Zone
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZonePresentationController:
    def __init__(
        self,
        logger: Logger,
        zone_manager: ZoneManagerProtocol,
        visualiser: ZoneVisualiserProtocol,
    ) -> None:
        self._logger = logger
        self._zone_manager = zone_manager
        self._visualiser = visualiser

        self.quit: Event[Callable[[], None]] = Event()

    async def start_async(self) -> None:
        self._zone_manager.current_zone_changed.subscribe(self._on_current_zone_changed)
        self._visualiser.quit.subscribe(self._on_visualiser_quit)
        self._visualiser.start()

    async def stop_async(self) -> None:
        self._visualiser.stop()
        self._visualiser.quit.unsubscribe(self._on_visualiser_quit)
        self._zone_manager.current_zone_changed.unsubscribe(self._on_current_zone_changed)

    def update(self) -> None:
        self._visualiser.update()

    def _on_current_zone_changed(self, zone: Zone | None) -> None:
        self._logger.debug(f"Presenting zone: {zone.id if zone else 'NONE'}")
        self._visualiser.show_zone(zone)

    def _on_visualiser_quit(self) -> None:
        self._logger.info("Zone visualiser quit requested")
        self.quit.invoke()
