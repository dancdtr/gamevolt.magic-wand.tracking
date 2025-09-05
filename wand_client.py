from collections.abc import Callable
from logging import Logger

from classification.gesture_type import GestureType
from detection.detected_gestures import DetectedGestures
from gamevolt.events.event import Event
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from messaging.detected_gesture_message import DetectedGesturesMessage


class WandClient:
    def __init__(self, logger: Logger, message_handler: MessageHandler) -> None:
        self._logger = logger
        self._message_handler = message_handler

        self.gesture_detected: Event[Callable[[DetectedGestures], None]] = Event()

    def start(self) -> None:
        self._message_handler.subscribe(DetectedGesturesMessage, self._on_gesture_message)

    def stop(self) -> None:
        self._message_handler.unsubscribe(DetectedGesturesMessage, self._on_gesture_message)

    def _on_gesture_message(self, message: Message) -> None:
        if isinstance(message, DetectedGesturesMessage):
            detection = DetectedGestures(duration=message.duration, types=[GestureType(name) for name in message.names])
            self.gesture_detected.invoke(detection)
