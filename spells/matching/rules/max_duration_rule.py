from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MaxDurationRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        m = ctx.metrics

        # if spell.max_total_duration_s is None:
        #     return True

        return m.total_duration_s <= spell.max_total_duration_s
