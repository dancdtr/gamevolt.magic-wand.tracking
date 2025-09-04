# rx.py
import asyncio
import time

from gamevolt_logging import get_logger

from detection.detected_gesture import DetectedGesture
from display.arrow_display import ArrowDisplay
from display.gesture_display import GestureDisplay
from display.gesture_image_library import GestureImageLibrary, ImageLibrarySettings
from gamevolt.display.configuration.image_visualiser_settings import ImageVisualiserSettings
from gamevolt.display.image_visualiser import ImageVisualiser
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp_message_receiver import UdpMessageReceiver
from wand_client import WandClient


async def main() -> None:

    logger = get_logger()
    message_receiver = UdpMessageReceiver(
        logger,
        rx=UdpRx(
            logger,
            settings=UdpRxSettings(
                host="127.0.0.1",
                port=9999,
                max_size=65536,
                recv_timeout_s=0.25,
            ),
        ),
    )
    message_handler = MessageHandler(logger, message_receiver)
    wand_client = WandClient(logger, message_handler)

    def on_gesture_detected(g: DetectedGesture) -> None:
        print(f"Show pic for: {g.type}")
        display.post(g.type)

    visualiser = ImageVisualiser(settings=ImageVisualiserSettings(300, 300, "Gestures", 60))
    image_library = GestureImageLibrary(settings=ImageLibrarySettings(assets_dir="./display/images/primitives", image_size=300))
    display = GestureDisplay(logger, image_library, visualiser)
    wand_client.gesture_detected.subscribe(on_gesture_detected)

    logger.info("Starting gesture visualiser...")
    display.start()
    message_handler.start()
    wand_client.start()

    try:
        while True:
            await asyncio.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Stopping gesture visualiser...")
        message_handler.stop()
        display.stop()
        logger.info("Stopped gesture visualiser.")


asyncio.run(main())
