# history/gesture_history.py
from __future__ import annotations

from collections import deque
from collections.abc import Callable

from detection.detected_gestures import DetectedGestures
from gamevolt.events.event import Event


class GestureHistory:
    def __init__(self, capacity: int):
        self._detections: deque[DetectedGestures] = deque(maxlen=capacity)

        self._is_complete = False

        self.updated: Event[Callable[[], None]] = Event()

    def append(self, detected_gesture: DetectedGestures) -> None:
        if self._is_complete:
            self.clear()
            self._is_complete = False

        self._detections.append(detected_gesture)
        self.updated.invoke()

    def clear(self) -> None:
        self._detections.clear()
        self.updated.invoke()

    def items(self) -> list[DetectedGestures]:
        return list(self._detections)

    def set_complete(self) -> None:
        self._is_complete = True
