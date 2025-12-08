from dataclasses import dataclass

from gamevolt.messaging.message import Message


@dataclass
class HelloMessage(Message):
    pass
