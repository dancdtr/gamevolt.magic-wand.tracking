from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class DistanceRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        s = ctx.spell
        m = ctx.metrics

        dist = m.total_distance + m.absorbed_distance

        if s.min_total_distance is not None and dist < s.min_total_distance:
            return False

        if s.max_total_distance is not None and dist > s.max_total_distance:
            return False

        return True
