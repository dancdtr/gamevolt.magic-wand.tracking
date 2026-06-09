from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from zones.visualisation.zone_visualiser_protocol import ZoneVisualiserProtocol
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZonePresentationController:
    """Bridges `ZoneManagerProtocol` enter/exit events to a zone visualiser.

    Tracks the most recently entered zone and shows it; clears the display
    when an exit event matches the currently shown zone. Good enough for the
    mock (all wands move together) and for production (`NullZoneVisualiser`
    has no UI to update). Multi-spell zones currently show the first spell
    via `ZoneVisualiserProtocol.show_zone`; richer multi-target UI is a
    future change.
    """

    def __init__(
        self,
        logger: Logger,
        zone_manager: ZoneManagerProtocol,
        visualiser: ZoneVisualiserProtocol,
    ) -> None:
        self._logger = logger
        self._zone_manager = zone_manager
        self._visualiser = visualiser

        self._shown_zone_id: str | None = None

        self.quit: Event[Callable[[], None]] = Event()

    @property
    def visualiser(self) -> ZoneVisualiserProtocol:
        return self._visualiser

    async def start_async(self) -> None:
        self._zone_manager.wand_entered_zone.subscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.subscribe(self._on_wand_exited_zone)
        self._visualiser.quit.subscribe(self._on_visualiser_quit)
        self._visualiser.start()

    async def stop_async(self) -> None:
        self._visualiser.stop()
        self._visualiser.quit.unsubscribe(self._on_visualiser_quit)
        self._zone_manager.wand_entered_zone.unsubscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.unsubscribe(self._on_wand_exited_zone)

    def update(self) -> None:
        self._visualiser.update()

    def _on_wand_entered_zone(self, wand_id: str, zone_id: str) -> None:
        if zone_id == self._shown_zone_id:
            return
        zone = self._zone_manager.get_zone(zone_id)
        self._shown_zone_id = zone_id
        self._logger.debug(f"Presenting zone: {zone_id}")
        self._visualiser.show_zone(zone)

    def _on_wand_exited_zone(self, wand_id: str, zone_id: str) -> None:
        if zone_id != self._shown_zone_id:
            return
        self._shown_zone_id = None
        self._logger.debug("Presenting zone: NONE")
        self._visualiser.show_zone(None)

    def _on_visualiser_quit(self) -> None:
        self._logger.info("Zone visualiser quit requested")
        self.quit.invoke()
