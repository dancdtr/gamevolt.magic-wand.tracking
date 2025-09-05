from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.message import Message
from gamevolt.messaging.message_receiver_protocol import MessageReceiverProtocol
from gamevolt.messaging.message_sender_protocol import MessageSenderProtocol
from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp.udp_tx import UdpTx


class UdpPeer(MessageReceiverProtocol, MessageSenderProtocol):
    def __init__(self, logger: Logger, settings: UdpPeerSettings) -> None:
        super().__init__()
        self._logger = logger

        self._tx = UdpTx(logger, settings.udp_tx)
        self._rx = UdpRx(logger, settings.udp_rx)

        self._message_received: Event[Callable[[str], None]] = Event()

    @property
    def message_received(self) -> Event[Callable[[str], None]]:
        return self._message_received

    def start(self) -> None:
        self._rx.message_received.subscribe(self._on_message_received)
        self._rx.start()

    def stop(self) -> None:
        self._rx.message_received.unsubscribe(self._on_message_received)
        self._rx.stop()

    def send(self, message: Message) -> None:
        self._tx.send(payload=message.to_dict())

    def _on_message_received(self, message: str) -> None:
        self._message_received.invoke(message)
