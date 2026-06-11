from __future__ import annotations

from dataclasses import dataclass

from spells.scoring.cast_score import CastScore
from spells.spell_cast_quality import SpellCastQuality
from spells.spell_type import SpellType


@dataclass(frozen=True)
class SpellCast:
    """Recognised-cast event payload: which wand cast which spell, and how well.

    Replaces the legacy step-group `SpellMatch`. Emitted only when a cast is recognised
    (gates passed + a quality tier awarded), so `score.quality` is never None here.
    """

    wand_id: str
    spell_type: SpellType
    score: CastScore

    @property
    def quality(self) -> SpellCastQuality:
        assert self.score.quality is not None  # guaranteed for a recognised cast
        return self.score.quality

    @property
    def spell_name(self) -> str:
        return self.spell_type.name
