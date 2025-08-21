# imu_binary_receiver.py

import struct
from collections.abc import Callable
from logging import Logger

from gamevolt.events.event import Event
from gamevolt.imu.configuration.imu_settings import ImuSettings
from gamevolt.imu.sensor_data import SensorData
from gamevolt.maths.vector_3 import Vector3
from gamevolt.serial.binary_serial_receiver import BinarySerialReceiver
from gamevolt.serial.configuration.binary_serial_receiver_settings import BinarySerialReceiverSettings


class IMUBinaryReceiver:
    """
    Listens for fixed-size binary packets and unpacks them into SensorData.
    """

    def __init__(self, logger: Logger, rx_settings: BinarySerialReceiverSettings, imu_settings: ImuSettings) -> None:
        self._logger = logger
        self._rx_settings = rx_settings.binary

        self._binary_rx = BinarySerialReceiver(logger, rx_settings)

        self.data_updated = Event[Callable[[SensorData], None]]()

        self._x_sign = -1 if imu_settings.flip_x else 1
        self._y_sign = -1 if imu_settings.flip_y else 1
        self._z_sign = -1 if imu_settings.flip_z else 1

    async def start(self) -> None:
        self._logger.info(f"IMU Binary Receiver starting...")
        self._binary_rx.data_received.subscribe(self._on_frame)
        await self._binary_rx.start()
        self._logger.info(f"IMU Binary Receiver started.")

    async def stop(self) -> None:
        await self._binary_rx.stop()
        self._binary_rx.data_received.unsubscribe(self._on_frame)

    def _on_frame(self, frame: bytes) -> None:
        unpacked = struct.unpack(self._rx_settings.packet_format, frame)

        ts = int(unpacked[0])

        ax, ay, az, gx, gy, gz, mx, my, mz = unpacked[1:]
        accel = Vector3(ax * self._x_sign, ay * self._y_sign, az * self._z_sign)
        gyro = Vector3(gx * self._x_sign, gy * self._y_sign, gz * self._z_sign)
        mag = Vector3(mx * self._x_sign, my * self._y_sign, mz * self._z_sign)

        data = SensorData(timestamp_ms=ts, accel=accel, gyro=gyro, mag=mag)

        self._logger.debug(data)
        self.data_updated.invoke(data)
