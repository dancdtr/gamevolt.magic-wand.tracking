# main.py

import asyncio
from asyncio import Queue
from typing import Optional

import numpy as np
from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from arrow_display import ArrowDisplay
from gamevolt.imu.imu_serial_receiver import IMUSerialReceiver
from gamevolt.imu.sensor_data import SensorData
from gamevolt.serial.configuration.binary_serial_receiver_settings import BinarySerialReceiverSettings
from gamevolt.serial.configuration.binary_settings import BinarySettings
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.imu_binary_receiver import IMUBinaryReceiver
from gamevolt.serial.serial_receiver import SerialReceiver

logger = get_logger(LoggingSettings("./Logs", "INFORMATION"))

display = ArrowDisplay()

# Flick thresholds
GYRO_START_THRESH = 1.0
GYRO_END_THRESH = 0.7
GYRO_END_FRAMES = 5

GUI_FPS = 60


# State
in_motion: bool = False
end_count: int = 0
last_data: Optional[SensorData] = None

# Queue to hand off flicks to the GUI
flick_queue: Queue[str] = Queue()

# x is roll (rotation around shaft) (-ve CCW, +ve CW)
# y is pitch (up and down) (-ve is up, +ve is down)
# z is yaw (left and right) (-ve is right, +ve is left)


def on_data(d: SensorData) -> None:
    global in_motion, end_count, last_data

    gx, gy, gz = d.gyro.x, d.gyro.y, d.gyro.z
    # mag = max(abs(gx), abs(gz))
    mag = max(abs(gy), abs(gz))

    if not in_motion:
        if mag > GYRO_START_THRESH:
            in_motion = True
            end_count = 0
            if abs(gx) > abs(gz):
                # direction = "up" if gx < 0 else "down"
                direction = "down" if gy > 0 else "up"
            else:
                direction = "left" if gz > 0 else "right"

            # use call_soon_threadsafe to put into the asyncio loop
            asyncio.get_event_loop().call_soon_threadsafe(flick_queue.put_nowait, direction)

    else:
        if mag < GYRO_END_THRESH:
            end_count += 1
            if end_count >= GYRO_END_FRAMES:
                in_motion = False
        else:
            end_count = 0

    last_data = d


async def gui_loop() -> None:
    """Update the GUI and process flick events."""
    current_direction: str | None = None
    while True:
        # show any queued flicks
        try:
            while True:
                direction = flick_queue.get_nowait()
                if direction and direction != current_direction:
                    current_direction = direction
                    # await asyncio.sleep(0.2)
                    display.show(direction)
        except asyncio.QueueEmpty:
            pass

        display.root.update()
        await asyncio.sleep(1 / GUI_FPS)


async def main() -> None:
    # start the GUI task in the same event loop
    asyncio.create_task(gui_loop())

    settings = BinarySerialReceiverSettings(
        SerialReceiverSettings(port="/dev/cu.usbmodem11101", baud=115200, timeout=1, retry_interval=3.0),
        BinarySettings("<I9f"),
    )
    imu_rx = IMUBinaryReceiver(logger, settings)

    imu_rx.data_updated.subscribe(on_data)

    await imu_rx.start()

    try:
        while True:
            await asyncio.sleep(0.02)
    finally:
        await imu_rx.stop()


if __name__ == "__main__":
    asyncio.run(main())
