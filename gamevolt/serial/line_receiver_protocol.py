from collections.abc import Callable
from typing import Protocol

from gamevolt.events.event import Event


class LineReceiverProtocol(Protocol):

    @property
    def line_received(self) -> Event[Callable[[str], None]]: ...

    async def start_async(self) -> None: ...
    async def stop_async(self) -> None: ...
