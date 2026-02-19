from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MaxDistanceRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        dist = ctx.metrics.total_distance

        return spell.max_total_distance is not None and dist <= spell.max_total_distance
