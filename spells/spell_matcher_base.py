from abc import ABC
from typing import Callable, Sequence

from gamevolt.events.event import Event
from motion.gesture_segment import GestureSegment
from spells.spell_match import SpellMatch


class SpellMatcherBase:
    @property
    def matched(self) -> Event[Callable[[SpellMatch], None]]: ...

    def try_match(self, history: Sequence[GestureSegment]) -> None: ...
