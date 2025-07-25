# main2.py

import asyncio
from asyncio import Queue
from typing import Optional

import numpy as np
from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from arrow_display import ArrowDisplay
from detection.configuration.gesture_detector_settings import GestureDetectorSettings
from detection.gesture_detector import GestureDetector
from gamevolt.imu.imu_serial_receiver import IMUSerialReceiver
from gamevolt.imu.sensor_data import SensorData
from gamevolt.serial.configuration.binary_serial_receiver_settings import BinarySerialReceiverSettings
from gamevolt.serial.configuration.binary_settings import BinarySettings
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gamevolt.serial.imu_binary_receiver import IMUBinaryReceiver
from vector_2 import Vector2

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


def on_gesture_completed(points: list[Vector2]) -> None:
    v = Vector2.from_average(points)
    # print(f"Average vector: {v}")

    abs_x = abs(v.x)
    abs_y = abs(v.y)

    # 2) Decide intercardinal vs cardinal
    # If the two components are within, say, ±20%, treat as intercardinal
    INTERCARDINAL_RATIO = 0.65  # 80% ≤ min/max ≤ 1.25 → roughly “equal”
    direction: str

    if abs_x > 0 and abs_y > 0 and (min(abs_x, abs_y) / max(abs_x, abs_y) >= INTERCARDINAL_RATIO):
        # Intercardinal: both axes active and similar magnitude
        if v.x > 0 and v.y > 0:
            direction = "down-left"
        elif v.x > 0 and v.y < 0:
            direction = "up-left"
        elif v.x < 0 and v.y < 0:
            direction = "up-right"
        else:  # v.x < 0 and v.y > 0
            direction = "down-right"

    else:
        # Pure cardinal: pick the dominant axis
        if abs_x > abs_y:
            direction = "left" if v.x > 0 else "right"
        else:
            direction = "down" if v.y > 0 else "up"

    print(f"Detected direction: {direction}")

    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(flick_queue.put_nowait, direction)


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


rx_settings = BinarySerialReceiverSettings(
    SerialReceiverSettings(port="/dev/cu.usbmodem11101", baud=115200, timeout=1, retry_interval=3.0),
    BinarySettings("<I9f"),
)
imu_rx = IMUBinaryReceiver(logger, rx_settings)

gesture_settings = GestureDetectorSettings(
    start_thresh=1.0,
    end_thresh=0.7,
    start_frames=3,
    end_frames=3,
    max_samples=100,
)
gesture_detector = GestureDetector(imu_rx, gesture_settings)


async def main() -> None:
    asyncio.create_task(gui_loop())

    gesture_detector.motion_ended.subscribe(on_gesture_completed)

    await imu_rx.start()
    gesture_detector.start()

    try:
        while True:
            await asyncio.sleep(0.02)
    finally:
        gesture_detector.stop()
        await imu_rx.stop()


if __name__ == "__main__":
    asyncio.run(main())
