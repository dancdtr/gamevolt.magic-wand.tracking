from collections.abc import Callable
from logging import Logger

from classification.gesture_type import GestureType
from detection.detected_gesture import DetectedGesture
from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from messaging.destected_gesture_message import DetectedGestureMessage


class WandClient:
    def __init__(self, logger: Logger, message_handler: MessageHandler) -> None:
        self._logger = logger
        self._message_handler = message_handler

        self.gesture_detected: Event[Callable[[DetectedGesture], None]] = Event()

    def start(self) -> None:
        self._message_handler.subscribe(DetectedGestureMessage, self._on_gesture_message)

    def stop(self) -> None:
        self._message_handler.unsubscribe(DetectedGestureMessage, self._on_gesture_message)

    def _on_gesture_message(self, message: Message) -> None:
        if isinstance(message, DetectedGestureMessage):
            detection = DetectedGesture(t_ms=message.ts, type=GestureType(message.name))
            self.gesture_detected.invoke(detection)
