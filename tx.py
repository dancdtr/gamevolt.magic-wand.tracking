import time

from gamevolt_logging import get_logger
from gamevolt_logging.configuration import LoggingSettings

from classification.gesture_type import GestureType
from gamevolt.messaging.udp.configuration.udp_tx_settings import UdpTxSettings
from gamevolt.messaging.udp.udp_tx import UdpTx
from gamevolt.messaging.udp_message_sender import UdpMessageSender
from messaging.detected_gesture_message import DetectedGesturesMessage

logger = get_logger(settings=LoggingSettings(minimum_level="DEBUG"))
settings = UdpTxSettings(host="127.0.0.1", port=9998)
tx = UdpTx(logger, settings)
message_sender = UdpMessageSender(logger, tx)

message_sender.start()
gestures = [g.name for g in GestureType]
i = 0
try:
    while True:
        msg = DetectedGesturesMessage(i, gestures[i % len(gestures)])
        message_sender.send(msg)
        i += 1
        time.sleep(1.0)
except KeyboardInterrupt:
    pass
