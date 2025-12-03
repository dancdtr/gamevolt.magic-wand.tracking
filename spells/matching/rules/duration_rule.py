from __future__ import annotations

from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class DurationRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        m = ctx.metrics

        key_duration = m.total_duration_s - m.filler_duration_s

        if spell.min_total_duration_s is not None and key_duration < spell.min_total_duration_s:
            return False

        if spell.max_total_duration_s is not None and key_duration > spell.max_total_duration_s:
            return False

        return True
