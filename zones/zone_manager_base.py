from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from zones.configuration.zones_settings import ZonesSettings
from zones.zone import Zone
from zones.zone_factory import ZoneFactory
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZoneManagerBase(ZoneManagerProtocol):
    """Shared zone bookkeeping for message-driven managers.

    Owns the `id -> Zone` map, the enter/exit events, and dedup of duplicate
    enters / stray exits via `Zone.wand_ids`. Subclasses own the ingress
    (which message type drives presence) and call `_enter` / `_exit`.
    """

    def __init__(self, logger: Logger, settings: ZonesSettings, zone_factory: ZoneFactory) -> None:
        self._wand_entered_zone: Event[Callable[[str, str], None]] = Event()
        self._wand_exited_zone: Event[Callable[[str, str], None]] = Event()

        self._logger = logger
        self._zones: dict[str, Zone] = {
            zone_settings.id: zone_factory.create(zone_settings.id, zone_settings.spells)
            for zone_settings in settings.zones
        }

    @property
    def wand_entered_zone(self) -> Event[Callable[[str, str], None]]:
        return self._wand_entered_zone

    @property
    def wand_exited_zone(self) -> Event[Callable[[str, str], None]]:
        return self._wand_exited_zone

    def get_zone(self, zone_id: str) -> Zone:
        zone = self._zones.get(zone_id.upper())
        if zone is None:
            raise KeyError(f"No zone with ID ({zone_id})!")
        return zone

    def zones_containing_wand(self, wand_id: str) -> list[str]:
        return [zone.id for zone in self._zones.values() if zone.contains_wand_id(wand_id)]

    def _enter(self, wand_id: str, zone_id: str) -> None:
        self._logger.debug(f"Wand ({wand_id}) entering zone ({zone_id})...")

        zone = self.get_zone(zone_id)
        if zone.contains_wand_id(wand_id):
            self._logger.warning(f"Wand ({wand_id}) is already present in zone ({zone_id})! Ignoring enter.")
            return

        zone.on_wand_enter(wand_id)
        self._wand_entered_zone.invoke(wand_id, zone.id)

    def _exit(self, wand_id: str, zone_id: str) -> None:
        self._logger.debug(f"Wand ({wand_id}) exiting zone ({zone_id})...")

        zone = self.get_zone(zone_id)
        if not zone.contains_wand_id(wand_id):
            self._logger.warning(f"Wand ({wand_id}) is not present in zone ({zone_id})! Ignoring exit.")
            return

        self._wand_exited_zone.invoke(wand_id, zone.id)
        zone.on_wand_exit(wand_id)
