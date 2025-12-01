from time import sleep

from gamevolt_logging import get_logger

from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from gamevolt.messaging.udp.configuration.udp_rx_settings import UdpRxSettings
from gamevolt.messaging.udp.udp_rx import UdpRx
from gamevolt.messaging.udp_message_receiver import UdpMessageReceiver
from messaging.detected_spell_message import DetectedSpellMessage

logger = get_logger()
rx = UdpRx(logger, UdpRxSettings("0.0.0.0", 8050, 65556, 3))
# message_receiver = UdpMessageReceiver(logger, rx)
# message_handler = MessageHandler(logger, message_receiver)


def on_spell_detected(message: str) -> None:
    logger.info(message)


# message_handler.subscribe(DetectedSpellMessage, on_spell_detected)
# message_handler.start()
rx.start()
while True:
    sleep(0.01)
