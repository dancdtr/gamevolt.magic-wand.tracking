from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class DurationRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        s = ctx.spell
        m = ctx.metrics

        action_s = m.scorable_duration_s + m.absorbed_duration_s

        if action_s < s.min_total_duration_s:
            return False

        # Keep max as wall-clock window duration (prevents “wait forever then finish”)
        if s.max_total_duration_s is not None and m.total_duration_s > s.max_total_duration_s:
            return False

        return True
