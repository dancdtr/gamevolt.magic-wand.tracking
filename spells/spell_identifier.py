from collections.abc import Callable
from logging import Logger

from detection.gesture_history import GestureHistory
from gamevolt.events.event import Event
from gamevolt.toolkit.timer import Timer
from spells.spell import Spell
from spells.spell_provider_base import SpellProviderBase
from spells.spell_type import SpellType

_SPELL_TIMEOUT = 1  # if a new gesture isnt received in this time then the gesture history is cleared


class SpellIdentifier:
    def __init__(self, logger: Logger, spell_provider: SpellProviderBase, gesture_history: GestureHistory) -> None:
        self._logger = logger

        self._gesture_history = gesture_history
        self._spell_provider = spell_provider

        self.spell_detected: Event[Callable[[Spell], None]] = Event()

        self._timer = Timer(_SPELL_TIMEOUT)

    def start(self) -> None:
        self._gesture_history.updated.subscribe(self._on_gestures_updated)
        self._spell_provider.target_spells_updated.subscribe(self._on_spells_updated)

        self._timer.start()

    def stop(self) -> None:
        self._gesture_history.updated.unsubscribe(self._on_gestures_updated)
        self._spell_provider.target_spells_updated.unsubscribe(self._on_spells_updated)

    def _on_gestures_updated(self) -> None:
        for spell in self._spell_provider.target_spells:
            expected_types = spell.definition

            if self._timer.is_complete:
                self._timer.start()
                self._gesture_history.clear_but_keep_last()  # discard expired gestures, keep only the newest

            self._timer.start()
            actual_detections = self._gesture_history.items()[-spell.length :]  # just take a relevant slice for now

            if len(expected_types) != len(actual_detections):
                return

            is_match = True

            for expected, detections in zip(expected_types, actual_detections):
                if expected not in detections.types:
                    is_match = False
                    break

            self._logger.debug(
                f"----------------------------------------\n"
                f"Checking spell: '{spell.name}':\n"
                f"Expected: {[gt.name for gt in expected_types]}\n"
                f"Actual: {[t.name for detection in actual_detections for t in detection.types]}\n"
                f"Is match: {'✅' if is_match else '❌'}\n"
                f"----------------------------------------"
            )

            duration = f"{sum([g.duration for g in actual_detections]) / 1000:.3f}ms"
            gesture_ids = [detection.gesture_id for detection in actual_detections]
            if is_match:
                self._logger.info(
                    f"'✅' Successfully identified spell ({spell.id}) '{spell.name}' with gestures: {gesture_ids}. Total duration={duration}."
                )
                self.spell_detected.invoke(spell)
                self._gesture_history.set_complete()
                return
            else:
                self._logger.info(
                    f"'❌' Failed to identify spell ({spell.id}) '{spell.name}' with gestures: {gesture_ids}. Total duration={duration}."
                )

    def _on_spells_updated(self, _: list[Spell]) -> None:
        self._gesture_history.clear()
