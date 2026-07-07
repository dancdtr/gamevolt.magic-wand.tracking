from __future__ import annotations

from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.udp_rx import UdpRx
from services.wand_session_coordinator import WandSessionCoordinator
from wand.streaming.eliko.wand_battery_monitor import WandBatteryMonitor
from wand.streaming.eliko.wand_reboot_detector import WandRebootDetector
from wand.streaming.wand_imu_stream import WandImuStream
from zones.zone_application import ZoneApplication


class TrackingApp:
    """Owns zone management, presence orchestration, and the IMU stream."""

    def __init__(
        self,
        logger: Logger,
        imu_stream: WandImuStream,
        zone_application: ZoneApplication,
        wand_session_coordinator: WandSessionCoordinator,
        zone_udp_receiver: UdpRx | None,
        zone_message_handler: MessageHandler | None,
        wand_reboot_detector: WandRebootDetector | None = None,
        wand_battery_monitor: WandBatteryMonitor | None = None,
    ) -> None:
        self.quit: Event[Callable[[], None]] = Event()

        self._logger = logger
        self._imu_stream = imu_stream
        self._zone_application = zone_application
        self._wand_session_coordinator = wand_session_coordinator
        self._zone_udp_receiver = zone_udp_receiver
        self._zone_message_handler = zone_message_handler
        self._wand_reboot_detector = wand_reboot_detector
        self._wand_battery_monitor = wand_battery_monitor

        self._zone_application.quit.subscribe(self._on_quit)

    async def start_async(self) -> None:
        if self._zone_udp_receiver is not None:
            await self._zone_udp_receiver.start_async()

        await self._zone_application.start_async()

        self._wand_session_coordinator.start()

        if self._zone_message_handler is not None:
            self._zone_message_handler.start()

        if self._wand_reboot_detector is not None:
            self._wand_reboot_detector.start()

        if self._wand_battery_monitor is not None:
            self._wand_battery_monitor.start()

        await self._imu_stream.start_async()

    async def stop_async(self) -> None:
        await self._imu_stream.stop_async()

        if self._wand_battery_monitor is not None:
            self._wand_battery_monitor.stop()

        if self._wand_reboot_detector is not None:
            self._wand_reboot_detector.stop()

        if self._zone_message_handler is not None:
            self._zone_message_handler.stop()
        self._wand_session_coordinator.stop()

        await self._zone_application.stop_async()

        if self._zone_udp_receiver is not None:
            await self._zone_udp_receiver.stop_async()

        self._zone_application.quit.unsubscribe(self._on_quit)

    def select_default_zone(self) -> None:
        """Apply the start-up zone selection; call once the full system is up."""
        self._zone_application.select_default_zone()

    def update(self) -> None:
        self._imu_stream.update()
        self._zone_application.update()

    def _on_quit(self) -> None:
        self._logger.info("TrackingApp quit requested")
        self.quit.invoke()
