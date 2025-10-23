from typing import Callable, Sequence

from analysis.spell_trace_api import SpellTrace
from gamevolt.events.event import Event
from motion.gesture_segment import GestureSegment
from spells.library.spell_difficulty_type import SpellDifficultyType
from spells.spell_match import SpellMatch
from spells.spell_matcher import SpellMatcher
from spells.spell_matcher_base import SpellMatcherBase


class SpellMatcherManager:
    def __init__(self, default_difficulty=SpellDifficultyType.FORGIVING) -> None:
        self._spell_matchers: dict[SpellDifficultyType, SpellMatcherBase] = {}
        self._difficulty = default_difficulty

        self.matched: Event[Callable[[SpellMatch], None]] = Event()

    def register(self, difficulty: SpellDifficultyType, matcher: SpellMatcherBase) -> None:
        matcher.matched.subscribe(self._on_match)
        self._spell_matchers[difficulty] = matcher

    def set_difficulty(self, difficulty: SpellDifficultyType) -> None:
        self._difficulty = difficulty

    def try_match(self, history: Sequence[GestureSegment], trace: SpellTrace) -> None:
        if not history:
            return

        matcher = self._spell_matchers.get(self._difficulty, None)
        if not matcher:
            raise KeyError(f"No spell matcher defined for difficulty: '{self._difficulty.name}'!")

        matcher.try_match(history, trace)

    def _on_match(self, match: SpellMatch) -> None:
        self.matched.invoke(match)
