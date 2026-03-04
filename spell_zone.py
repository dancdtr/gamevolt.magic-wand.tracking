from logging import Logger

from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from wand.wand_server import WandServer
from zones.zone_entered_message import ZoneEnteredMessage
from zones.zone_exited_message import ZoneExitedMessage


class SpellZone:
    def __init__(self, logger: Logger, zone_udp_handler: MessageHandler, wand_server: WandServer) -> None:
        self._zone_udp_handler = zone_udp_handler
        self._wand_server = wand_server
        self._logger = logger

    def start(self) -> None:
        self._zone_udp_handler.subscribe(ZoneEnteredMessage, self._on_wand_entered_message)
        self._zone_udp_handler.subscribe(ZoneExitedMessage, self._on_wand_exited_message)
        self._zone_udp_handler.start()

    def stop(self) -> None:

        self._zone_udp_handler.stop()
        self._zone_udp_handler.unsubscribe(ZoneExitedMessage, self._on_wand_entered_message)
        self._zone_udp_handler.unsubscribe(ZoneExitedMessage, self._on_wand_exited_message)

    def update(self) -> None:
        pass

    def _on_wand_entered_message(self, message: Message) -> None:
        if isinstance(message, ZoneEnteredMessage):
            self._wand_server.add_wand_id(message.WandId)

    def _on_wand_exited_message(self, message: Message) -> None:
        if isinstance(message, ZoneExitedMessage):
            self._wand_server.remove_wand_id(message.WandId)
