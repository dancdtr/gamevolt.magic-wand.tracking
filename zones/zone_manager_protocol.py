from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from gamevolt.events.event import Event
from zones.zone import Zone


class ZoneManagerProtocol(ABC):
    @property
    @abstractmethod
    def zone_entered(self) -> Event[Callable[[Zone, str], None]]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def zone_exited(self) -> Event[Callable[[Zone, str], None]]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def current_zone_changed(self) -> Event[Callable[[Zone | None], None]]:
        raise NotImplementedError()

    @abstractmethod
    async def start_async(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def stop_async(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_zone(self, id: str) -> Zone:
        raise NotImplementedError()

    @abstractmethod
    def get_zone_containing_wand_id(self, id: str) -> Zone:
        raise NotImplementedError()

    @abstractmethod
    def on_wand_disconnected(self, wand_id: str) -> None:
        raise NotImplementedError()
