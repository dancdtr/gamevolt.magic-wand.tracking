from __future__ import annotations

from logging import Logger

from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from messaging.active_wand_changed import ActiveWandChanged
from zones.configuration.zones_settings import ZonesSettings
from zones.zone_factory import ZoneFactory
from zones.zone_manager_base import ZoneManagerBase

_ACTIVE_STATE = "ACTIVE"
_INACTIVE_STATE = "INACTIVE"


class ActiveWandZoneManager(ZoneManagerBase):
    """RTLS zone presence driven by a single `ActiveWandChanged` event.

    The RTLS system owns which wand is the active caster in a zone; `state`
    carries enter (`ACTIVE`) vs exit (`INACTIVE`). Presence is keyed on
    `zone_id`. Incoming `wand_id` is normalised to bare upper hex so the
    `0x`-prefixed wire form matches the app's internal wand ids.
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
        self._message_handler.subscribe(ActiveWandChanged, self._on_active_wand_changed)

    async def stop_async(self) -> None:
        self._message_handler.unsubscribe(ActiveWandChanged, self._on_active_wand_changed)

    def _on_active_wand_changed(self, message: Message) -> None:
        if not isinstance(message, ActiveWandChanged):
            return

        wand_id = self._normalise_wand_id(message.wand_id)
        state = message.state.strip().upper()

        if state == _ACTIVE_STATE:
            self._enter(wand_id, message.zone_id)
        elif state == _INACTIVE_STATE:
            self._exit(wand_id, message.zone_id)
        else:
            self._logger.warning(f"ActiveWandChanged for wand ({wand_id}) has unknown state '{message.state}'. Ignoring.")

    @staticmethod
    def _normalise_wand_id(raw: str) -> str:
        s = raw.strip()
        if s.lower().startswith("0x"):
            s = s[2:]
        # RTLS pads the tag serial with leading zeros (e.g. 0x001DAC) while the
        # app's canonical ids are bare short hex (1DAC). Trim so the two match.
        s = s.lstrip("0") or s
        return s.upper()
