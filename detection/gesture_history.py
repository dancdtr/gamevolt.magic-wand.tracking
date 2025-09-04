# history/gesture_history.py
from __future__ import annotations

from collections import deque
from collections.abc import Callable

from detection.detected_gesture import DetectedGesture
from gamevolt.events.event import Event


class GestureHistory:
    def __init__(self, capacity: int = 10):
        self._items: deque[DetectedGesture] = deque(maxlen=capacity)
        self.updated: Event[Callable[[], None]] = Event()

    def append(self, detected_gesture: DetectedGesture) -> None:
        print(f"appending img to history for: {detected_gesture.type.name}")
        self._items.append(detected_gesture)
        self.updated.invoke()

    def clear(self) -> None:
        self._items.clear()
        self.updated.invoke()

    def items(self) -> list[DetectedGesture]:
        return list(self._items)
