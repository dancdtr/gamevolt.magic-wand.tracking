from cdtr_rtls.anchor_area_entered import AnchorAreaEnteredMessage
from cdtr_rtls.anchor_area_exited import AnchorAreaExitedMessage
from cdtr_rtls.configuration.anchor_area_manager_settings import AnchorAreaManagerSettings
from gamevolt.logging import Logger
from gamevolt.messaging.message import Message
from gamevolt.web_sockets.web_socket_server import WebSocketServer
from zones.zone_manager_protocol import ZoneManagerProtocol


class AnchorAreaManager:
    """Routes wand commands to the anchor servicing the wand's current zone.

    Configured with zone_id → anchor_id mappings; listens to zone presence
    events so it can forward anchor-area enter/exit notifications and look
    up the right anchor when commands target a specific wand.
    """

    def __init__(
        self,
        logger: Logger,
        settings: AnchorAreaManagerSettings,
        zone_manager: ZoneManagerProtocol,
        web_socket_server: WebSocketServer,
    ) -> None:
        self._web_socket_server = web_socket_server
        self._zone_manager = zone_manager
        self._settings = settings
        self._logger = logger

        self._mappings: dict[str, str] = {}

        for anchor_area in settings.anchor_areas:
            for zone_id in anchor_area.zone_ids:
                self._mappings[zone_id] = anchor_area.id

    def start(self) -> None:
        self._zone_manager.wand_entered_zone.subscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.subscribe(self._on_wand_exited_zone)

    def stop(self) -> None:
        self._zone_manager.wand_entered_zone.unsubscribe(self._on_wand_entered_zone)
        self._zone_manager.wand_exited_zone.unsubscribe(self._on_wand_exited_zone)

    def broadcast_to_wand(self, wand_id: str, message: Message) -> None:
        anchor_ids = self._web_socket_server.connected_clients.keys()
        self._logger.verbose(f"Broadcasting {message.MessageType} to wand ({wand_id}) via all connected anchors ({anchor_ids})...")
        self._web_socket_server.broadcast(message)

    def send_to_wand(self, wand_id: str, message: Message) -> None:
        anchor_id = self._get_anchor_id_for_wand(wand_id)
        self._logger.verbose(f"Sending {message.MessageType} to wand ({wand_id}) via anchor ({anchor_id})...")
        self._web_socket_server.send_to_client(anchor_id, message)

    def _on_wand_entered_zone(self, wand_id: str, zone_id: str) -> None:
        anchor_id = self._get_anchor_id_for_zone(zone_id)
        self._logger.info(f"Wand ({wand_id}) has entered anchor area ({anchor_id}).")
        self._web_socket_server.send_to_client(anchor_id, AnchorAreaEnteredMessage(anchor_id, wand_id))

    def _on_wand_exited_zone(self, wand_id: str, zone_id: str) -> None:
        anchor_id = self._get_anchor_id_for_zone(zone_id)
        self._logger.info(f"Wand ({wand_id}) has exited anchor area ({anchor_id}).")
        self._web_socket_server.send_to_client(anchor_id, AnchorAreaExitedMessage(anchor_id, wand_id))

    def _get_anchor_id_for_wand(self, wand_id: str) -> str:
        zone_ids = self._zone_manager.zones_containing_wand(wand_id)
        if not zone_ids:
            raise KeyError(f"Wand ({wand_id}) is not present in any zone!")
        # If the wand straddles overlapping zones, route via the first mapped anchor.
        return self._get_anchor_id_for_zone(zone_ids[0])

    def _get_anchor_id_for_zone(self, zone_id: str) -> str:
        anchor_id = self._mappings.get(zone_id)
        if anchor_id is None:
            raise KeyError(f"No anchor area mapped for zone ID: ({zone_id})!")
        return anchor_id
