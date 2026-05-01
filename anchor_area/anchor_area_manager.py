from collections.abc import Callable

from anchor_area.anchor_area_entered import AnchorAreaEnteredMessage
from anchor_area.anchor_area_exited import AnchorAreaExitedMessage
from anchor_area.configuration.anchor_area_manager_settings import AnchorAreaManagerSettings
from gamevolt.events.event import Event
from gamevolt.logging import Logger
from gamevolt.messaging.message import Message
from gamevolt.web_sockets.web_socket_client_meta import WebSocketClientMeta
from gamevolt.web_sockets.web_socket_server import WebSocketServer
from zones.zone import Zone
from zones.zone_manager_protocol import ZoneManagerProtocol


class AnchorAreaManager:
    def __init__(
        self, logger: Logger, settings: AnchorAreaManagerSettings, zone_manager: ZoneManagerProtocol, web_socket_server: WebSocketServer
    ) -> None:
        self._web_socket_server = web_socket_server
        self._zone_manager = zone_manager
        self._settings = settings
        self._logger = logger

        self.anchor_connected_for_wand: Event[Callable[[str, str], None]] = Event()

        self._mappings: dict[str, str] = {}
        self._reverse_mappings: dict[str, list[str]] = {}

        for anchor_area in settings.anchor_areas:
            self._reverse_mappings[anchor_area.id] = list(anchor_area.zone_ids)
            for zone_id in anchor_area.zone_ids:
                self._mappings[zone_id] = anchor_area.id

    def start(self) -> None:
        self._zone_manager.zone_entered.subscribe(self._on_zone_entered)
        self._zone_manager.zone_exited.subscribe(self._on_zone_exited)
        self._web_socket_server.client_connected.subscribe(self._on_client_connected)

        for anchor_id in list(self._web_socket_server.connected_clients.keys()):
            self._replay_zone_state_for_anchor(anchor_id)

    def stop(self) -> None:
        self._zone_manager.zone_exited.unsubscribe(self._on_zone_entered)
        self._zone_manager.zone_exited.unsubscribe(self._on_zone_exited)
        self._web_socket_server.client_connected.unsubscribe(self._on_client_connected)

    def broadcast_message(self, message: Message) -> None:
        pass

    def blast_message_to_wand(self, wand_id: str, message: Message) -> None:
        anchor_ids = self._web_socket_server.connected_clients.keys()
        self._logger.verbose(f"Broadcasting {message.MessageType} to wand ({wand_id}) via all connected anchors ({anchor_ids})...")
        self._web_socket_server.broadcast(message)

    def relay_message_to_wand(self, wand_id: str, message: Message) -> None:
        anchor_id = self._get_anchor_id_handling_wand_id(wand_id)
        self._logger.verbose(f"Sending {message.MessageType} to wand ({wand_id}) via anchor ({anchor_id})...")

        self._web_socket_server.send_to_client(anchor_id, message)

    def _on_zone_entered(self, zone: Zone, wand_id: str) -> None:
        anchor_id = self._get_anchor_id(zone)
        self._logger.info(f"Wand ({wand_id}) has entered anchor area ({anchor_id}).")

        self._web_socket_server.send_to_client(anchor_id, AnchorAreaEnteredMessage(anchor_id, wand_id))

    def _on_zone_exited(self, zone: Zone, wand_id: str) -> None:
        anchor_id = self._get_anchor_id(zone)
        self._logger.info(f"Wand ({wand_id}) has exited anchor area ({anchor_id}).")

        self._web_socket_server.send_to_client(anchor_id, AnchorAreaExitedMessage(anchor_id, wand_id))

    def _on_client_connected(self, client_meta: WebSocketClientMeta) -> None:
        self._replay_zone_state_for_anchor(client_meta.id)

    def _replay_zone_state_for_anchor(self, anchor_id: str) -> None:
        zone_ids = self._reverse_mappings.get(anchor_id)
        if not zone_ids:
            return

        for zone_id in zone_ids:
            try:
                zone = self._zone_manager.get_zone(zone_id)
            except KeyError:
                continue
            for wand_id in zone.wand_ids:
                self._logger.info(f"Anchor ({anchor_id}) connected; replaying zone ({zone_id}) state for wand ({wand_id}).")
                self._web_socket_server.send_to_client(anchor_id, AnchorAreaEnteredMessage(anchor_id, wand_id))
                self.anchor_connected_for_wand.invoke(anchor_id, wand_id)

    def _get_anchor_id_handling_wand_id(self, wand_id: str) -> str:
        zone = self._zone_manager.get_zone_containing_wand_id(wand_id)
        return self._get_anchor_id(zone)

    def _get_anchor_id(self, zone: Zone) -> str:
        anchor_id = self._mappings.get(zone.id)
        if anchor_id is None:
            raise KeyError(f"No anchor area mapped for zone ID: ({zone.id})!")

        return anchor_id
