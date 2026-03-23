from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from gamevolt.events.event import Event
from spells.spell_type import SpellType
from zones.zone import Zone


class ZoneVisualiserProtocol(ABC):
    @property
    @abstractmethod
    def quit(self) -> Event[Callable[[], None]]:
        raise NotImplementedError()

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def update(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def show_zone(self, zone: Zone | None) -> None:
        raise NotImplementedError()

    @abstractmethod
    def show_spell_instruction(self, spell_type: SpellType) -> None:
        raise NotImplementedError()

    @abstractmethod
    def show_spell_cast(self, spell_type: SpellType) -> None:
        raise NotImplementedError()

    @abstractmethod
    def show_spell_cast_coloured(self, spell_type: SpellType, colour: str) -> None:
        raise NotImplementedError()
