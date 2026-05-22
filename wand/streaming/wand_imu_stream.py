from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from gamevolt.events.event import Event
from wand.data.assembled_packet import AssembledPacket


class WandImuStream(Protocol):
    @property
    def packet_received(self) -> Event[Callable[[AssembledPacket], None]]: ...

    async def start_async(self) -> None: ...
    async def stop_async(self) -> None: ...
    def update(self) -> None: ...
