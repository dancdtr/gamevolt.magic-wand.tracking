from dataclasses import dataclass
from typing import Sequence

from motion.gesture.gesture_segment import GestureSegment
from spells.matching.spell_match_metrics import SpellMatchMetrics
from spells.spell_definition import SpellDefinition


@dataclass(frozen=True)
class SpellMatchContext:
    spell: SpellDefinition
    segments: Sequence[GestureSegment]
    metrics: SpellMatchMetrics

    # Index of oldest segment used in this match (0 = oldest overall segment)
    window_start_index: int
    # Index of newest segment used in this match
    window_end_index: int
