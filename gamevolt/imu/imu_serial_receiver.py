import re
from collections.abc import Callable

from gamevolt.events.event import Event
from gamevolt.imu.sensor_data import SensorData
from gamevolt.serial.serial_receiver import SerialReceiver
from vector_3 import Vector3


class IMUSerialReceiver:
    LINE_REGEX = re.compile(
        r"""
        ^\s*                                # optional leading whitespace
        t=\s*(?P<loopt>\d+)\s*ms\s*\|\s*
        a=\[\s*(?P<ax>[-\d.]+)\s*,\s*(?P<ay>[-\d.]+)\s*,\s*(?P<az>[-\d.]+)\]\s*g\s*\|\s*
        g=\[\s*(?P<gx>[-\d.]+)\s*,\s*(?P<gy>[-\d.]+)\s*,\s*(?P<gz>[-\d.]+)\]\s*°/s\s*\|\s*
        m=\[\s*(?P<mx>[-\d.]+)\s*,\s*(?P<my>[-\d.]+)\s*,\s*(?P<mz>[-\d.]+)\]\s*[µμ]T\s*$
        """,
        re.VERBOSE,
    )

    def __init__(self, serial_receiver: SerialReceiver) -> None:
        self._serial_receiver = serial_receiver

        self.data_updated = Event[Callable[[SensorData], None]]()

    async def start(self) -> None:
        self._serial_receiver.data_received.subscribe(self._on_data_received)
        await self._serial_receiver.start()

    async def stop(self) -> None:
        await self._serial_receiver.stop()
        self._serial_receiver.data_received.unsubscribe(self._on_data_received)

    def _on_data_received(self, line: str) -> None:
        m = self.LINE_REGEX.search(line)
        if not m:
            return

        ts = int(m.group(1))
        ax, ay, az = map(float, m.group(2, 3, 4))
        gx, gy, gz = map(float, m.group(5, 6, 7))
        mx, my, mz = map(float, m.group(8, 9, 10))

        data = SensorData(
            timestamp_ms=ts,
            accel=Vector3(ax, ay, az),
            gyro=Vector3(gx, gy, gz),
            mag=Vector3(mx, my, mz),
        )
        self.data_updated.invoke(data)
