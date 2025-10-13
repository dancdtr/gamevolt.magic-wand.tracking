# main.py

import asyncio

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from classification.gesture_classifier_controller import GestureClassifierController
from detection.configuration.gesture_detector_settings import GestureDetectorSettings
from detection.configuration.gesture_settings import GestureSettings
from detection.gesture_detector import GestureDetector
from detection.gesture_factory import GestureFactory
from detection.gesture_func_provider import GestureFuncProvider
from gamevolt.imu.configuration.imu_settings import ImuSettings
from gamevolt.imu.imu_binary_receiver import IMUBinaryReceiver
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.configuration.udp_peer_settings import UdpPeerSettings
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp_peer import UdpPeer
from gamevolt.serial.configuration.binary_serial_receiver_settings import BinarySerialReceiverSettings
from gamevolt.serial.configuration.binary_settings import BinarySettings
from gamevolt.serial.configuration.serial_receiver_settings import SerialReceiverSettings
from gestures.gesture_point import GesturePoint
from messaging.detected_gesture_message import DetectedGesturesMessage

logger = get_logger(LoggingSettings("./Logs/wand_tracking.log", "INFORMATION"))

GYRO_START_THRESH = 1.0
GYRO_END_THRESH = 0.7
GYRO_END_FRAMES = 5


rx_settings = BinarySerialReceiverSettings(
    SerialReceiverSettings(port="/dev/cu.usbmodem2101", baud=115200, timeout=1, retry_interval=3.0),
    BinarySettings("<I9f"),
)

# imu_settings = ImuSettings(flip_x=True, flip_y=True, flip_z=True)
imu_settings = ImuSettings(flip_x=False, flip_y=False, flip_z=False)
imu_rx = IMUBinaryReceiver(logger, rx_settings, imu_settings)
udp_peer = UdpPeer(
    logger,
    settings=UdpPeerSettings(
        udp_tx=UdpTxSettings(
            host="127.0.0.1",
            port=9998,
        ),
        udp_rx=UdpRxSettings(
            host="127.0.0.1",
            port=9999,
            max_size=65536,
            recv_timeout_s=0.25,
        ),
    ),
)

gesture_settings = GestureDetectorSettings(
    start_thresh=1.0,
    end_thresh=0.7,
    start_frames=2,
    end_frames=2,
    max_samples=200,
    min_duration=0.14,
)
gesture_detector = GestureDetector(logger, imu_rx, gesture_settings)

message_handler = MessageHandler(logger, udp_peer)

func_provider = GestureFuncProvider(logger)
gesture_identifier = GestureClassifierController(logger, func_provider, message_handler)
gesture_factory = GestureFactory(logger, settings=GestureSettings())


def on_gesture_completed(points: list[GesturePoint]) -> None:
    gesture = gesture_factory.create(points)
    gesture_types = gesture_identifier.identify(gesture)

    gesture_names = [g.name for g in gesture_types]
    logger.debug(f"Identified gestures: {gesture_names}")

    udp_peer.send(DetectedGesturesMessage(id=gesture.id, duration=gesture.duration, names=gesture_names))


async def main() -> None:
    logger.info("Starting Wand Tracking application...")
    gesture_detector.motion_ended.subscribe(on_gesture_completed)

    await imu_rx.start()
    udp_peer.start()
    gesture_detector.start()
    gesture_identifier.start()
    message_handler.start()

    try:
        while True:
            await asyncio.sleep(0.02)
    except asyncio.exceptions.CancelledError:
        logger.info("Stopping Wand Tracking application...")
    finally:
        gesture_detector.stop()
        await imu_rx.stop()
        logger.info("Stopped Wand Tracking application.")


# if __name__ == "__main__":
asyncio.run(main())
