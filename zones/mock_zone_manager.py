from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from zones.configuration.zones_settings import ZonesSettings
from zones.zone import Zone
from zones.zone_factory import ZoneFactory
from zones.zone_manager_protocol import ZoneManagerProtocol


class MockZoneManager(ZoneManagerProtocol):
    """Mock zone presence driven by `set_current_zone` (typically from a UI).

    Loads the same zone list production uses (`ZonesSettings.zones`), keeps
    a single global "current zone" at any time, and toggles every tracked
    wand into / out of that zone in one shot. Picks a different zone via
    `set_current_zone(zone_id)`; clear with `set_current_zone(None)`.
    """

    def __init__(
        self,
        logger: Logger,
        settings: ZonesSettings,
        zone_factory: ZoneFactory,
        wand_ids: list[str],
    ) -> None:
        self._wand_entered_zone: Event[Callable[[str, str], None]] = Event()
        self._wand_exited_zone: Event[Callable[[str, str], None]] = Event()

        self._logger = logger
        self._wand_ids = list(wand_ids)

        self._zones: dict[str, Zone] = {
            zone_settings.id: zone_factory.create(zone_settings.id, zone_settings.spells)
            for zone_settings in settings.zones
        }

        self._current_zone_id: str | None = None

    @property
    def wand_entered_zone(self) -> Event[Callable[[str, str], None]]:
        return self._wand_entered_zone

    @property
    def wand_exited_zone(self) -> Event[Callable[[str, str], None]]:
        return self._wand_exited_zone

    async def start_async(self) -> None:
        self._logger.info("MockZoneManager started")

    async def stop_async(self) -> None:
        self._logger.info("MockZoneManager stopped")

    def get_zone(self, zone_id: str) -> Zone:
        zone = self._zones.get(zone_id.upper())
        if zone is None:
            raise KeyError(f"No zone with ID ({zone_id})!")
        return zone

    def zones_containing_wand(self, wand_id: str) -> list[str]:
        return [self._current_zone_id] if self._current_zone_id is not None else []

    def set_current_zone(self, zone_id: str | None) -> None:
        """Swap every tracked wand out of the prior zone (if any) and into the new one."""
        if zone_id is not None:
            # Validate before touching state so a typo doesn't strand wands in limbo.
            self.get_zone(zone_id)

        prior_zone_id = self._current_zone_id
        if prior_zone_id == zone_id:
            return

        if prior_zone_id is not None:
            prior_zone = self._zones[prior_zone_id]
            for wand_id in self._wand_ids:
                prior_zone.on_wand_exit(wand_id)
                self._wand_exited_zone.invoke(wand_id, prior_zone_id)

        self._current_zone_id = zone_id

        if zone_id is not None:
            new_zone = self._zones[zone_id]
            for wand_id in self._wand_ids:
                new_zone.on_wand_enter(wand_id)
                self._wand_entered_zone.invoke(wand_id, zone_id)
