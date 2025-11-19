from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class DurationRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        duration = ctx.metrics.total_duration_s

        if spell.min_total_duration_s is not None and duration < spell.min_total_duration_s:
            return False

        if spell.max_total_duration_s is not None and duration > spell.max_total_duration_s:
            return False

        return True
