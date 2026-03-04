from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from zones.zone_entered_message import ZoneEnteredMessage
from zones.zone_exited_message import ZoneExitedMessage


class ZoneServer:
    def __init__(self, logger: Logger, message_handler: MessageHandler) -> None:
        self.wand_entered_zone: Event[Callable[[str, str], None]] = Event()  # zone_id, wand_id
        self.wand_exited_zone: Event[Callable[[str, str], None]] = Event()  # zone_id, wand_id

        self._message_handler = message_handler
        self._logger = logger

    def start(self) -> None:
        self._message_handler.subscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.subscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)
        self._message_handler.start()

    def stop(self) -> None:
        self._message_handler.stop()
        self._message_handler.unsubscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.unsubscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    def _on_wand_entered_zone_message(self, message: Message):
        if isinstance(message, ZoneEnteredMessage):
            zone_id, wand_id = message.ZoneId, message.WandId

            self._logger.debug(f"Wand ({wand_id}) entered zone ({zone_id}).")
            self.wand_entered_zone.invoke(zone_id, wand_id)

    def _on_wand_exited_zone_message(self, message: Message):
        if isinstance(message, ZoneExitedMessage):
            zone_id, wand_id = message.ZoneId, message.WandId

            self._logger.debug(f"Wand ({wand_id}) exited zone ({zone_id}).")
            self.wand_exited_zone.invoke(zone_id, wand_id)
