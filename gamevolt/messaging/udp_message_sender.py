from logging import Logger

from gamevolt.messaging.message import Message
from gamevolt.messaging.message_sender_protocol import MessageSenderProtocol
from gamevolt.messaging.udp.udp_tx import UdpTx


class UdpMessageSender(MessageSenderProtocol):
    def __init__(self, logger: Logger, udp_tx: UdpTx) -> None:
        self._logger = logger
        self._udp_tx = udp_tx

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def send(self, message: Message) -> None:
        self._logger.debug(f"Sending message: {message}")
        self._udp_tx.send(payload=message.to_dict())
