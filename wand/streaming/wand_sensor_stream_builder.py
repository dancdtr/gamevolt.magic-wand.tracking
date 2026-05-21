from __future__ import annotations

from gamevolt.logging import Logger
from gamevolt.serial.line_receiver_protocol import LineReceiverProtocol
from wand.streaming.configuration.wand_sensor_stream_settings import WandSensorStreamSettings
from wand.streaming.line_based_wand_sensor_stream import LineBasedWandSensorStream
from wand.streaming.wand_sensor_stream import WandSensorStream


class WandSensorStreamBuilder:
    def __init__(self, logger: Logger, settings: WandSensorStreamSettings) -> None:
        self._logger = logger
        self._settings = settings

    def build_line_based(self, line_receiver: LineReceiverProtocol) -> WandSensorStream:
        return LineBasedWandSensorStream(
            logger=self._logger,
            line_receiver=line_receiver,
            header_ttl_s=self._settings.header_ttl_s,
        )
