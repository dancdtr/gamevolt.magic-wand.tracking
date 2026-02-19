from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MinDurationRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        m = ctx.metrics
        spell = ctx.spell

        key_duration = m.total_duration_s - m.filler_duration_s

        return spell.min_total_duration_s is not None and key_duration >= spell.min_total_duration_s
