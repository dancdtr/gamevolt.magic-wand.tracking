# main.py

import asyncio
from asyncio import Queue

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from classification.classifiers.gesture_classifier_mask import GestureClassifierMask
from classification.gesture_classifier import GestureClassifier
from classification.gesture_type import GestureType
from detection.configuration.gesture_detector_settings import GestureDetectorSettings
from detection.configuration.gesture_settings import GestureSettings
from detection.gesture_detector import GestureDetector
from detection.gesture_factory import GestureFactory
from detection.gesture_point import GesturePoint
from display.arrow_display import ArrowDisplay
from gamevolt.imu.configuration.imu_settings import ImuSettings
from gamevolt.imu.imu_binary_receiver import IMUBinaryReceiver
from gamevolt.imu.imu_serial_receiver import IMUSerialReceiver
from gamevolt.imu.sensor_data import SensorData
from gamevolt.serial.configuration.binary_serial_receiver_settings import BinarySerialReceiverSettings
from gamevolt.serial.configuration.binary_settings import BinarySettings
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from spell_checker import SpellChecker

logger = get_logger(LoggingSettings("./Logs/wand_tracking.log", "INFORMATION"))

display = ArrowDisplay(image_size=300, assets_dir="./display/images/primitives", title="Wand Gesture Display")

GYRO_START_THRESH = 1.0
GYRO_END_THRESH = 0.7
GYRO_END_FRAMES = 5
GUI_FPS = 60


in_motion: bool = False
end_count: int = 0

# Queue to hand off flicks to the GUI
flick_queue: Queue[GestureType] = Queue()

# x is roll (rotation around shaft) (-ve CCW, +ve CW)
# y is pitch (up and down) (-ve is up, +ve is down)
# z is yaw (left and right) (-ve is right, +ve is left)

classifier = GestureClassifier(logger)


gesture_factory = GestureFactory(settings=GestureSettings())
spell_checker = SpellChecker(logger)


def on_gesture_completed(points: list[GesturePoint]) -> None:
    gesture = gesture_factory.create(points)
    gesture_types = classifier.classify(gesture)

    matches = [g.name for g in gesture_types]
    logger.debug(f"Matched gestures: {matches}")
    gesture_type = gesture_types[0]
    logger.debug(f"Using gesture: {gesture_type.name}")
    # print("____________________________________________________________")

    # spell checker:
    if gesture_type not in (GestureType.NONE, GestureType.UNKNOWN):
        spell_checker.update_gestures(gesture_type)
        # if spell_checker.check_silencio():
        #     logger.info("✨✨✨ SILENCIO!!! ✨✨✨")
        #     spell_checker.purge_gestures()
        # elif spell_checker.check_revelio():
        #     logger.info("✨✨✨ REVELIO!!! ✨✨✨")
        #     spell_checker.purge_gestures()
        if spell_checker.check_locomotor():
            logger.info("✨✨✨ LOCOMOTOR!!! 🟢 ✨✨✨")
            spell_checker.purge_gestures()
        elif spell_checker.check_arresto_momentum():
            logger.info("✨✨✨ ARRESTO MOMENTUM!!! 🔴 ✨✨✨")
            spell_checker.purge_gestures()

    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(flick_queue.put_nowait, gesture_type)


async def gui_loop() -> None:
    """Update the GUI and process flick events."""
    current_gesture: GestureType = GestureType.NONE
    while True:
        try:
            while True:
                gesture = flick_queue.get_nowait()
                if gesture and gesture != current_gesture:
                    current_gesture = gesture
                    # await asyncio.sleep(0.2)
                    display.show(gesture)
        except asyncio.QueueEmpty:
            pass

        display.root.update()
        await asyncio.sleep(1 / GUI_FPS)


rx_settings = BinarySerialReceiverSettings(
    SerialReceiverSettings(port="/dev/cu.usbmodem11101", baud=115200, timeout=1, retry_interval=3.0),
    BinarySettings("<I9f"),
)

# imu_settings = ImuSettings(flip_x=True, flip_y=True, flip_z=True)
imu_settings = ImuSettings(flip_x=False, flip_y=False, flip_z=False)
imu_rx = IMUBinaryReceiver(logger, rx_settings, imu_settings)

gesture_settings = GestureDetectorSettings(
    start_thresh=1.0,
    end_thresh=0.7,
    start_frames=3,
    end_frames=3,
    max_samples=100,
    min_duration=0.14,
)
gesture_detector = GestureDetector(logger, imu_rx, gesture_settings)


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
