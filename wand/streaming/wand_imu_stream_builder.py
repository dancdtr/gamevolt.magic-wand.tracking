from __future__ import annotations

from gamevolt.logging import Logger
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from wand.streaming.configuration.wand_imu_stream_settings import WandImuStreamSettings
from wand.streaming.line_based_wand_imu_stream import LineBasedWandImuStream
from wand.streaming.wand_imu_stream import WandImuStream


class WandImuStreamBuilder:
    def __init__(self, logger: Logger, settings: WandImuStreamSettings) -> None:
        self._logger = logger
        self._settings = settings

    def build_line_based(self, line_receiver: LineReceiverProtocol) -> WandImuStream:
        return LineBasedWandImuStream(
            logger=self._logger,
            line_receiver=line_receiver,
            header_ttl_s=self._settings.header_ttl_s,
        )
