# rx.py
import time

from gamevolt_logging import get_logger

from display.arrow_display import ArrowDisplay
from display.gesture_image_library import GestureImageLibrary, ImageLibrarySettings
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp_message_receiver import UdpMessageReceiver
from wand_client import WandClient

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

message_handler.start()
wand_client.start()

display = ArrowDisplay(logger, image_size=300, assets_dir="./display/images/primitives", title="Wand Gesture Display")


logger.info("Starting gesture visualiser...")
try:
    while True:
        time.sleep(0.25)
except KeyboardInterrupt:
    pass
finally:
    logger.info("Stopping gesture visualiser...")
    message_handler.stop()
    logger.info("Stopped gesture visualiser.")
