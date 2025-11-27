from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class RequiredStepsRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        return ctx.metrics.required_matched == ctx.metrics.required_total
