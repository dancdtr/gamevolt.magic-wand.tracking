from collections.abc import Callable
from typing import Protocol

from gamevolt.events.event import Event


class MessageReceiverProtocol(Protocol):
    @property
    def message_received(self) -> Event[Callable[[str], None]]: ...

    async def start_async(self) -> None: ...

    async def stop_async(self) -> None: ...
