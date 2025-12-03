from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class MinDurationRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        m = ctx.metrics

        print("checking min duration rule")

        print(
            f"Total: {m.total_duration_s:.2f} {m.filler_duration_s:2f} = {m.total_duration_s - m.filler_duration_s} | min: {spell.min_total_duration_s}"
        )

        return m.total_duration_s - m.filler_duration_s > spell.min_total_duration_s
