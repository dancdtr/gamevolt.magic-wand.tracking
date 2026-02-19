from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MinDistanceRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        dist = ctx.metrics.total_distance

        return spell.min_total_distance is not None and dist >= spell.min_total_distance
