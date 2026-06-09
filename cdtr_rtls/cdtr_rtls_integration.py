from __future__ import annotations

from cdtr_rtls.anchor_area_manager import AnchorAreaManager
from cdtr_rtls.configuration.anchor_area_manager_settings import AnchorAreaManagerSettings
from cdtr_rtls.web_socket_line_receiver import WebSocketLineReceiver
from gamevolt.logging import Logger
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from gamevolt.web_sockets.configuration.web_socket_server_settings import WebSocketServerSettings
from gamevolt.web_sockets.web_socket_server import WebSocketServer
from wand.wand_command_sink import WandCommandSink
from zones.zone_manager_protocol import ZoneManagerProtocol


class CdtrRtlsIntegration:
    """Bundles every cdtr-rtls-specific dependency in one place.

    The main app talks to this through two seams:
      - `wand_command_sink` — `WandCommandSink` impl that knows how to route
        commands to the right anchor based on the wand's current zone.
      - `imu_line_source` — `LineReceiverProtocol` impl that surfaces lines
        the relay anchors forward over WebSocket; consumed by the line-based
        IMU stream.

    Anchor-area concepts (zone↔anchor mapping, anchor-area enter/exit
    messages, the relay WebSocket server) all live inside this class. The
    main app's `TrackingApp` / `RecognitionApp` never reference them.

    Lifecycle: start the integration **before** `TrackingApp.start_async()`
    so the WebSocket server is accepting relay connections by the time the
    IMU stream subscribes; stop **after** `TrackingApp.stop_async()`.
    """

    def __init__(
        self,
        logger: Logger,
        anchor_area_settings: AnchorAreaManagerSettings,
        web_socket_server_settings: WebSocketServerSettings,
        zone_manager: ZoneManagerProtocol,
    ) -> None:
        self._logger = logger

        self._web_socket_server = WebSocketServer(logger, web_socket_server_settings)
        self._anchor_area_manager = AnchorAreaManager(
            logger=logger,
            settings=anchor_area_settings,
            zone_manager=zone_manager,
            web_socket_server=self._web_socket_server,
        )
        self._imu_line_source = WebSocketLineReceiver(logger=logger, web_socket_server=self._web_socket_server)

    @property
    def wand_command_sink(self) -> WandCommandSink:
        return self._anchor_area_manager

    @property
    def imu_line_source(self) -> LineReceiverProtocol:
        return self._imu_line_source

    async def start_async(self) -> None:
        await self._web_socket_server.start_async()
        self._anchor_area_manager.start()

    async def stop_async(self) -> None:
        self._anchor_area_manager.stop()
        await self._web_socket_server.stop_async()
