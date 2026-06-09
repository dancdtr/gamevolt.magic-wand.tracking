from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from gamevolt.events.event import Event
from zones.zone import Zone


class ZoneManagerProtocol(ABC):
    """Per-wand zone presence service.

    Production drives enter/exit from real positioning (UDP today, position
    stream tomorrow); mock drives them from a UI dropdown. Consumers receive
    `(wand_id, zone_id)` and look up zone metadata (spell types, etc.) via
    `get_zone(zone_id)` when they need it.
    """

    @property
    @abstractmethod
    def wand_entered_zone(self) -> Event[Callable[[str, str], None]]:
        """Fires `(wand_id, zone_id)` when a wand enters a zone."""

    @property
    @abstractmethod
    def wand_exited_zone(self) -> Event[Callable[[str, str], None]]:
        """Fires `(wand_id, zone_id)` when a wand exits a zone."""

    @abstractmethod
    async def start_async(self) -> None: ...

    @abstractmethod
    async def stop_async(self) -> None: ...

    @abstractmethod
    def get_zone(self, zone_id: str) -> Zone:
        """Look up zone metadata. Raises KeyError if unknown."""

    @abstractmethod
    def zones_containing_wand(self, wand_id: str) -> list[str]:
        """Zone ids the wand currently occupies. Empty list if none."""
