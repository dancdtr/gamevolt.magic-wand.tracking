from logging import Logger
from typing import Callable, Sequence

from gamevolt.events.event import Event
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol


class MultiLineReceiver(LineReceiverProtocol):
    def __init__(self, logger: Logger, line_receivers: Sequence[LineReceiverProtocol]) -> None:
        self._line_received: Event[Callable[[str], None]] = Event()

        self._serial_receivers = line_receivers
        self._logger = logger

    @property
    def line_received(self) -> Event[Callable[[str], None]]:
        return self._line_received

    async def start(self) -> None:
        for serial_receiver in self._serial_receivers:
            serial_receiver.line_received.subscribe(self._on_line_received)

        for serial_receiver in self._serial_receivers:
            await serial_receiver.start()

    async def stop(self) -> None:
        for serial_receiver in self._serial_receivers:
            await serial_receiver.stop()

        for serial_receiver in self._serial_receivers:
            serial_receiver.line_received.unsubscribe(self._on_line_received)

    def _on_line_received(self, line: str) -> None:
        self._line_received.invoke(line)
