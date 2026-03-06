from logging import Logger
from typing import Callable

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
    def __init__(self, logger: Logger, settings: ZonesSettings, message_handler: MessageHandler, zone_factory: ZoneFactory) -> None:
        self.zone_entered: Event[Callable[[str, str], None]] = Event()
        self.zone_exited: Event[Callable[[str, str], None]] = Event()

        self._message_handler = message_handler
        self._zone_factory = zone_factory
        self._logger = logger

        self._zones: dict[str, Zone] = {}
        for id, spell_type in settings.zones:
            self._zones[id] = self._zone_factory.create(id, spell_type)

    async def start_async(self) -> None:
        self._message_handler.subscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.subscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)
        await self._message_handler.start_async()

    async def stop_async(self) -> None:
        await self._message_handler.stop_async()
        self._message_handler.unsubscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.unsubscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    def get_zone(self, id: str) -> Zone:
        zone = self._zones.get(id)
        if zone is None:
            raise KeyError(f"No zone with ID: ({id})!")

        return zone

    def on_wand_connected(self, wand_id: str) -> None:
        return super().on_wand_connected(wand_id)

    def on_wand_disconnected(self, wand_id: str) -> None:
        for zone in self._zones.values():
            if zone.contains_wand(wand_id):
                zone.on_wand_disconnected(wand_id)

    def _on_wand_entered_zone_message(self, message: Message):
        if isinstance(message, ZoneEnteredMessage):
            zone_id, wand_id = message.ZoneId, message.WandId

            self._logger.debug(f"Wand ({wand_id}) entered zone ({zone_id}).")

            self.get_zone(zone_id).on_wand_enter(wand_id)
            self.zone_entered.invoke(zone_id, wand_id)

    def _on_wand_exited_zone_message(self, message: Message):
        if isinstance(message, ZoneExitedMessage):
            zone_id, wand_id = message.ZoneId, message.WandId

            self._logger.debug(f"Wand ({wand_id}) exited zone ({zone_id}).")

            self.get_zone(zone_id).on_wand_exit(wand_id)

            self.zone_exited.invoke(zone_id, wand_id)
