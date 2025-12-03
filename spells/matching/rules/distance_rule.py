from __future__ import annotations

from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class DistanceRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        dist = ctx.metrics.total_distance

        if spell.min_total_distance is not None and dist < spell.min_total_distance:
            return False

        if spell.max_total_distance is not None and dist > spell.max_total_distance:
            return False

        return True
