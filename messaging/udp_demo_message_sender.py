from logging import Logger

from gamevolt.messaging.message import Message
from gamevolt.messaging.message_sender_protocol import MessageSenderProtocol
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx


class DemoUdpMessageSender(MessageSenderProtocol):
    def __init__(self, logger: Logger, settings: UdpTxSettings) -> None:
        self._logger = logger
        self._settings = settings

        self._udp_tx = UdpTx(logger, settings)

    def start(self) -> None:
        self._logger.info(f"Starting Udp Message Sender targeting '{self._settings.address}'...")

    def stop(self) -> None:
        self._logger.info(f"Stopping Udp Message Sender targeting '{self._settings.address}'.")

    def send(self, message: Message) -> None:
        self._logger.debug(f"Sending message: {message}")
        self._udp_tx.send(payload=message.to_dict())
        print(message.to_dict())
