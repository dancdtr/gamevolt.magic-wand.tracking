from __future__ import annotations

from logging import Logger

from anchor_area.anchor_area import AnchorArea
from anchor_area.anchor_area_entered import AnchorAreaEnteredMessage
from anchor_area.anchor_area_exited import AnchorAreaExitedMessage
from gamevolt.messaging.events.message_handler import MessageHandler


class AnchorAreaController:
    def __init__(self, logger: Logger, message_handler: MessageHandler, anchor_area: AnchorArea, anchor_id: str) -> None:
        self._message_handler = message_handler
        self._anchor_area = anchor_area
        self._anchor_id = anchor_id
        self._logger = logger

    def start(self) -> None:
        self._message_handler.subscribe_typed(AnchorAreaEnteredMessage, self._on_area_entered)
        self._message_handler.subscribe_typed(AnchorAreaExitedMessage, self._on_area_exited)

    def stop(self) -> None:
        self._message_handler.unsubscribe_typed(AnchorAreaEnteredMessage, self._on_area_entered)
        self._message_handler.unsubscribe_typed(AnchorAreaExitedMessage, self._on_area_exited)

    def _on_area_entered(self, message: AnchorAreaEnteredMessage) -> None:
        if not self._is_for_this_area(message.AreaId):
            return

        wand_id = message.WandId.upper()
        self._anchor_area.enter(wand_id)

        self._logger.info(f"({wand_id}) entered zone '{message.AreaId}'")
        self._logger.debug(f"Wands in zone '{message.AreaId}': {self._anchor_area.ids()}")

    def _on_area_exited(self, message: AnchorAreaExitedMessage) -> None:
        if not self._is_for_this_area(message.AreaId):
            return

        wand_id = message.WandId.upper()
        self._anchor_area.exit(wand_id)

        self._logger.info(f"({wand_id}) exited zone '{message.AreaId}'")

    def _is_for_this_area(self, zone_id: str) -> bool:
        if self._anchor_id is None:
            return True
        return zone_id.upper() == self._anchor_id
