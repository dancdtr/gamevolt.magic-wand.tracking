# main2.py

import asyncio
from asyncio import Queue
from typing import Optional

import numpy as np
from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from arrow_display import ArrowDisplay
from classification.curve_classifier import CurveClassifier
from classification.first_quarant_classifier import FirstQuadrantClassifier
from classification.intercardinal_classifier import IntercardinalClassifier
from classification.simple_classifier import SimpleClassifier
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

classifier = IntercardinalClassifier()
classifier2 = FirstQuadrantClassifier()
classifier3 = SimpleClassifier()
classifier4 = CurveClassifier()


def on_gesture_completed(points: list[Vector2]) -> None:
    direction = classifier.classify(points)
    print(f"Detected direction: {direction}")
    print("---")
    dir2 = classifier4.classify(points)
    print(dir2)
    print("xxx")

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
    logger.info("Starting Wand Tracking application...")
    asyncio.create_task(gui_loop())

    gesture_detector.motion_ended.subscribe(on_gesture_completed)

    await imu_rx.start()
    gesture_detector.start()

    try:
        while True:
            await asyncio.sleep(0.02)
    except asyncio.exceptions.CancelledError:
        logger.info("Stopping Wand Tracking application...")
    finally:
        gesture_detector.stop()
        await imu_rx.stop()
        logger.info("Stopped Wand Tracking application.")


if __name__ == "__main__":
    asyncio.run(main())
