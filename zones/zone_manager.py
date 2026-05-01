from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from gamevolt.web_sockets.web_socket_server import WebSocketServer
from zones.configuration.zones_settings import ZonesSettings
from zones.zone import Zone
from zones.zone_entered_message import ZoneEnteredMessage
from zones.zone_exited_message import ZoneExitedMessage
from zones.zone_factory import ZoneFactory
from zones.zone_manager_protocol import ZoneManagerProtocol


class ZoneManager(ZoneManagerProtocol):
    def __init__(
        self,
        logger: Logger,
        settings: ZonesSettings,
        message_handler: MessageHandler,
        zone_factory: ZoneFactory,
        web_socket_server: WebSocketServer,
    ) -> None:
        self._current_zone_changed: Event[Callable[[Zone | None], None]] = Event()
        self._zone_entered: Event[Callable[[Zone, str], None]] = Event()
        self._zone_exited: Event[Callable[[Zone, str], None]] = Event()

        self._web_socket_server = web_socket_server
        self._message_handler = message_handler
        self._zone_factory = zone_factory
        self._logger = logger

        self._zones: dict[str, Zone] = {}
        for zone_settings in settings.zones:
            self._zones[zone_settings.id] = self._zone_factory.create(zone_settings.id, zone_settings.spells)

    @property
    def zone_entered(self) -> Event[Callable[[Zone, str], None]]:
        return self._zone_entered

    @property
    def zone_exited(self) -> Event[Callable[[Zone, str], None]]:
        return self._zone_exited

    async def start_async(self) -> None:
        self._message_handler.subscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.subscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    async def stop_async(self) -> None:
        self._message_handler.unsubscribe(ZoneEnteredMessage, self._on_wand_entered_zone_message)
        self._message_handler.unsubscribe(ZoneExitedMessage, self._on_wand_exited_zone_message)

    def get_zone(self, id: str) -> Zone:
        zone = self._zones.get(id.upper())
        if zone is None:
            raise KeyError(f"No zone with ID ({id})!")

        return zone

    def get_zone_containing_wand_id(self, wand_id: str) -> Zone:
        for zone in self._zones.values():
            if zone.contains_wand_id(wand_id):
                return zone

        raise KeyError(f"No zone containing wand ID ({wand_id})!")

    def pin_wand(self, zone_id: str, wand_id: str) -> None:
        zone = self.get_zone(zone_id)
        if zone.contains_wand_id(wand_id):
            return

        zone.on_wand_enter(wand_id)
        self._logger.info(f"Wand ({wand_id}) pinned to zone ({zone_id}).")
        self._zone_entered.invoke(zone, wand_id)

    @property
    def current_zone_changed(self) -> Event[Callable[[Zone | None], None]]:
        return self._current_zone_changed

    def on_wand_disconnected(self, wand_id: str) -> None:
        return
        for zone in self._zones.values():
            if zone.contains_wand(wand_id):
                zone.on_wand_disconnected(wand_id)

    def _on_wand_entered_zone_message(self, message: Message):
        if isinstance(message, ZoneEnteredMessage):
            zone_id, wand_id = message.ZoneId, message.WandId
            self._logger.debug(f"Wand ({wand_id}) entering zone ({zone_id}..).")

            zone = self.get_zone(zone_id)
            is_wand_in_zone = zone.contains_wand_id(wand_id)

            if is_wand_in_zone:
                self._logger.warning(f"Wand ({wand_id}) is already present in zone ({zone_id})! Ignoring enter.")
                return

            zone.on_wand_enter(wand_id)
            self.zone_entered.invoke(zone, wand_id)

    def _on_wand_exited_zone_message(self, message: Message):
        if isinstance(message, ZoneExitedMessage):
            zone_id, wand_id = message.ZoneId, message.WandId
            self._logger.debug(f"Wand ({wand_id}) exiting zone ({zone_id})...")

            zone = self.get_zone(zone_id)
            is_wand_in_zone = zone.contains_wand_id(wand_id)

            if not is_wand_in_zone:
                self._logger.warning(f"Wand ({wand_id}) is not present in zone ({zone_id})! Ignoring exit.")
                return

            self.zone_exited.invoke(zone, wand_id)
            zone.on_wand_exit(wand_id)
