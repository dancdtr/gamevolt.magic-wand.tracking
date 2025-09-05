from collections.abc import Callable
from logging import Logger

from detection.gesture_history import GestureHistory
from gamevolt.events.event import Event
from input.spell_provider import SpellProviderBase
from spell_type import SpellType


class SpellChecker:
    def __init__(self, logger: Logger, spell_provider: SpellProviderBase, gesture_history: GestureHistory) -> None:
        self._logger = logger

        self._gesture_history = gesture_history
        self._spell_provider = spell_provider

        self.spell_detected: Event[Callable[[SpellType], None]] = Event()

    def start(self) -> None:
        self._gesture_history.updated.subscribe(self._on_gestures_updated)

    def stop(self) -> None:
        self._gesture_history.updated.unsubscribe(self._on_gestures_updated)

    def clear_gestures(self) -> None:
        self._gesture_history.clear()

    def _on_gestures_updated(self) -> None:
        for spell in self._spell_provider.target_spells:
            expected_types = spell.definition
            actual_detections = self._gesture_history.items()[-spell.length :]  # just take a relevant slice for now

            if len(expected_types) != len(actual_detections):
                return

            is_match = False

            for expected, detections in zip(expected_types, actual_detections):
                if expected not in detections.types:
                    break
                is_match = True

            self._logger.debug(
                f"----------------------------------------"
                f"Checking spell '{spell.name}':"
                f"Expected: {[gt.name for gt in expected_types]}"
                f"Actual: {[detection.types for detection in actual_detections]}"
                f"Is match: {'✅' if is_match else '❌'}"
                f"----------------------------------------"
            )

            self.spell_detected.invoke(spell.type)
            self.clear_gestures()
            return
