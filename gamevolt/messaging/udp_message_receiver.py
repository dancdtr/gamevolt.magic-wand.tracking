from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.message import Message
from gamevolt.messaging.message_receiver_protocol import MessageReceiverProtocol
from gamevolt.messaging.udp.udp_rx import UdpRx


class UdpMessageReceiver(MessageReceiverProtocol):
    def __init__(self, logger: Logger, rx: UdpRx) -> None:
        self._logger = logger
        self._udp_rx = rx

        self._message_received: Event[Callable[[str], None]] = Event()

    @property
    def message_received(self) -> Event[Callable[[str], None]]:
        return self._message_received

    def start(self) -> None:
        self._udp_rx.message_received.subscribe(self._on_data_received)
        self._udp_rx.start()

    def stop(self) -> None:
        self._udp_rx.message_received.unsubscribe(self._on_data_received)
        self._udp_rx.stop()

    def _on_data_received(self, data: str) -> None:
        self._logger.info(f"RX ← {data}")
        self.message_received.invoke(data)
