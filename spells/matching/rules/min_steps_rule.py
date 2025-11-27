from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MinStepsRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        return ctx.metrics.used_steps >= ctx.spell.min_spell_steps
