from collections.abc import Callable
from typing import Protocol

from gamevolt.events.event import Event
from gamevolt.messaging.message import Message


class MessageReceiverProtocol(Protocol):
    @property
    def message_received(self) -> Event[Callable[[str], None]]: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...
