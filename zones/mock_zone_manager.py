from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from spells.spell import Spell
from spells.spell_registry import SpellRegistry
from zones.zone import Zone
from zones.zone_manager_protocol import ZoneManagerProtocol


class MockZoneManager(ZoneManagerProtocol):
    def __init__(
        self,
        logger: Logger,
        spell_registry: SpellRegistry,
        wand_ids: list[str],
    ) -> None:
        self._spell_registry = spell_registry
        self._wand_ids = wand_ids
        self._logger = logger

        self._current_zone_changed: Event[Callable[[Zone | None], None]] = Event()
        self._zone_entered: Event[Callable[[Zone, str], None]] = Event()
        self._zone_exited: Event[Callable[[Zone, str], None]] = Event()

        self._current_zone: Zone | None = None

    @property
    def zone_entered(self) -> Event[Callable[[Zone, str], None]]:
        return self._zone_entered

    @property
    def zone_exited(self) -> Event[Callable[[Zone, str], None]]:
        return self._zone_exited

    @property
    def current_zone_changed(self) -> Event[Callable[[Zone | None], None]]:
        return self._current_zone_changed

    async def start_async(self) -> None:
        self._logger.info("MockZoneManager started")

    async def stop_async(self) -> None:
        self._logger.info("MockZoneManager stopped")

    def on_wand_disconnected(self, wand_id: str) -> None:
        pass

    def set_spell(self, spell: Spell) -> None:
        self._logger.debug(f"Mock zone spell set to {spell.type.name}")

        if self._current_zone is not None:
            for wand_id in self._wand_ids:
                self._current_zone.on_wand_exit(wand_id)
                self._zone_exited.invoke(self._current_zone, wand_id)

        zone_id = f"Z0{'0' if 10 >spell.id > 0 else''}{spell.id}"
        self._current_zone = Zone(self._logger, zone_id, spell_types=[spell.type])

        for wand_id in self._wand_ids:
            self._current_zone.on_wand_enter(wand_id)
            self._zone_entered.invoke(self._current_zone, wand_id)

        self._current_zone_changed.invoke(self._current_zone)

    def get_zone(self, id: str) -> Zone:
        if self._current_zone is None:
            raise RuntimeError(f"NO ZONE SET!")

        return self._current_zone

    def get_zone_containing_wand_id(self, id: str) -> Zone:
        return self.get_zone(id)

    # def clear_zone(self) -> None:
    #     if self._current_zone is not None:
    #         for wand_id in self._wand_ids:
    #             self._current_zone.on_wand_exit(wand_id)
    #             self._zone_exited.invoke(self._current_zone, wand_id)

    #     self._current_zone = None
    #     self._current_zone_changed.invoke(None)
