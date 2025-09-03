from typing import Protocol

from gamevolt.messaging.message import Message


class MessageSenderProtocol(Protocol):
    def send(self, message: Message) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...
