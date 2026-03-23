from __future__ import annotations

from collections.abc import Callable

from gamevolt.events.event import Event
from spells.spell_type import SpellType
from zones.visualisation.zone_visualiser_protocol import ZoneVisualiserProtocol
from zones.zone import Zone


class NullZoneVisualiser(ZoneVisualiserProtocol):
    def __init__(self) -> None:
        self._quit: Event[Callable[[], None]] = Event()

    @property
    def quit(self) -> Event[Callable[[], None]]:
        return self._quit

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def update(self) -> None:
        pass

    def show_zone(self, zone: Zone | None) -> None:
        pass

    def show_spell_instruction(self, spell_type: SpellType) -> None:
        pass

    def show_spell_cast(self, spell_type: SpellType) -> None:
        pass

    def show_spell_cast_coloured(self, spell_type: SpellType, colour: str) -> None:
        pass
