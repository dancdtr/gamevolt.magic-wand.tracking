from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from zones.configuration.zones_settings import ZonesSettings
from zones.zone import Zone
from zones.zone_entered_message import ZoneEnteredMessage
from zones.zone_exited_message import ZoneExitedMessage
from zones.zone_factory import ZoneFactory
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZoneManager(ZoneManagerProtocol):
    """Production zone presence driven by UDP `ZoneEnteredMessage` / `ZoneExitedMessage`.

    Tracks per-zone wand presence via the `Zone.wand_ids` set, so duplicate
    enters and stray exits are deduped/logged rather than re-emitted.
    """

    def __init__(
        self,
        logger: Logger,
        settings: ZonesSettings,
        message_handler: MessageHandler,
        zone_factory: ZoneFactory,
    ) -> None:
        self._wand_entered_zone: Event[Callable[[str, str], None]] = Event()
        self._wand_exited_zone: Event[Callable[[str, str], None]] = Event()

        self._message_handler = message_handler
        self._logger = logger

        self._zones: dict[str, Zone] = {
            zone_settings.id: zone_factory.create(zone_settings.id, zone_settings.spells)
            for zone_settings in settings.zones
        }

    @property
    def wand_entered_zone(self) -> Event[Callable[[str, str], None]]:
        return self._wand_entered_zone

    @property
    def wand_exited_zone(self) -> Event[Callable[[str, str], None]]:
        return self._wand_exited_zone

    async def start_async(self) -> None:
        self._message_handler.subscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.subscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    async def stop_async(self) -> None:
        self._message_handler.unsubscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.unsubscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    def get_zone(self, zone_id: str) -> Zone:
        zone = self._zones.get(zone_id.upper())
        if zone is None:
            raise KeyError(f"No zone with ID ({zone_id})!")
        return zone

    def zones_containing_wand(self, wand_id: str) -> list[str]:
        return [zone.id for zone in self._zones.values() if zone.contains_wand_id(wand_id)]

    def _on_wand_entered_zone_message(self, message: Message) -> None:
        if not isinstance(message, ZoneEnteredMessage):
            return

        zone_id, wand_id = message.ZoneId, message.WandId
        self._logger.debug(f"Wand ({wand_id}) entering zone ({zone_id})...")

        zone = self.get_zone(zone_id)
        if zone.contains_wand_id(wand_id):
            self._logger.warning(f"Wand ({wand_id}) is already present in zone ({zone_id})! Ignoring enter.")
            return

        zone.on_wand_enter(wand_id)
        self._wand_entered_zone.invoke(wand_id, zone.id)

    def _on_wand_exited_zone_message(self, message: Message) -> None:
        if not isinstance(message, ZoneExitedMessage):
            return

        zone_id, wand_id = message.ZoneId, message.WandId
        self._logger.debug(f"Wand ({wand_id}) exiting zone ({zone_id})...")

        zone = self.get_zone(zone_id)
        if not zone.contains_wand_id(wand_id):
            self._logger.warning(f"Wand ({wand_id}) is not present in zone ({zone_id})! Ignoring exit.")
            return

        self._wand_exited_zone.invoke(wand_id, zone.id)
        zone.on_wand_exit(wand_id)
