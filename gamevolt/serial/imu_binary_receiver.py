# imu_binary_receiver.py

import struct
from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.imu.sensor_data import SensorData
from gamevolt.maths.vector_3 import Vector3
from gamevolt.serial.binary_serial_receiver import BinarySerialReceiver
from gamevolt.serial.configuration.binary_serial_receiver_settings import BinarySerialReceiverSettings


class IMUBinaryReceiver:
    """
    Listens for fixed-size binary packets and unpacks them into SensorData.
    """

    def __init__(self, logger: Logger, settings: BinarySerialReceiverSettings) -> None:
        self._logger = logger

        self._binary_rx = BinarySerialReceiver(logger, settings)
        self._settings = settings.binary

        self.data_updated = Event[Callable[[SensorData], None]]()

    async def start(self) -> None:
        self._logger.info(f"IMU Binary Receiver starting...")
        self._binary_rx.data_received.subscribe(self._on_frame)
        await self._binary_rx.start()
        self._logger.info(f"IMU Binary Receiver started.")

    async def stop(self) -> None:
        await self._binary_rx.stop()
        self._binary_rx.data_received.unsubscribe(self._on_frame)

    def _on_frame(self, frame: bytes) -> None:
        unpacked = struct.unpack(self._settings.packet_format, frame)
        ts = int(unpacked[0])
        ax, ay, az, gx, gy, gz, mx, my, mz = unpacked[1:]

        data = SensorData(
            timestamp_ms=ts,
            accel=Vector3(ax, ay, az),
            gyro=Vector3(gx, gy, gz),
            mag=Vector3(mx, my, mz),
        )
        self._logger.debug(data)
        self.data_updated.invoke(data)
