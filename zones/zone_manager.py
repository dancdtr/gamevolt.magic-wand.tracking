from __future__ import annotations

from logging import Logger

from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from zones.configuration.zones_settings import ZonesSettings
from zones.zone_entered_message import ZoneEnteredMessage
from zones.zone_exited_message import ZoneExitedMessage
from zones.zone_factory import ZoneFactory
from zones.zone_manager_base import ZoneManagerBase


class ZoneManager(ZoneManagerBase):
    """Zone presence driven by UDP `ZoneEnteredMessage` / `ZoneExitedMessage`.

    Generic enter/exit ingress. The RTLS deployment instead uses
    `ActiveWandZoneManager` (single `ActiveWandChanged` event).
    """

    def __init__(
        self,
        logger: Logger,
        settings: ZonesSettings,
        message_handler: MessageHandler,
        zone_factory: ZoneFactory,
    ) -> None:
        super().__init__(logger=logger, settings=settings, zone_factory=zone_factory)
        self._message_handler = message_handler

    async def start_async(self) -> None:
        self._message_handler.subscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.subscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    async def stop_async(self) -> None:
        self._message_handler.unsubscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.unsubscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    def _on_wand_entered_zone_message(self, message: Message) -> None:
        if not isinstance(message, ZoneEnteredMessage):
            return
        self._enter(message.WandId, message.ZoneId)

    def _on_wand_exited_zone_message(self, message: Message) -> None:
        if not isinstance(message, ZoneExitedMessage):
            return
        self._exit(message.WandId, message.ZoneId)
