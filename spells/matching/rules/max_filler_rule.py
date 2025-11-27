from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MaxFillerRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        m = ctx.metrics

        if spell.max_filler_duration_s <= 0:
            return True

        return m.filler_duration_s <= spell.max_filler_duration_s
