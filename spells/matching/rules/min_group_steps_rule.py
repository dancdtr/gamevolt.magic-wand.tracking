from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MinGroupStepsRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        mins = [g.min_steps for g in ctx.spell.step_groups]
        matched = ctx.metrics.group_steps_matched

        for i, min_steps in enumerate(mins):
            if min_steps <= 0:
                continue
            if i >= len(matched):
                return False
            if matched[i] < min_steps:
                return False

        return True
