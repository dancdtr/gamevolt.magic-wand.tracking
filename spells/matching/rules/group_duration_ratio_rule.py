from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class GroupDurationRatioRule(SpellRule):

    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        metrics = ctx.metrics

        # TODO
        return True

        # total = max(metrics.total_duration_s, spell.min_total_duration_s)

        # for gi, group in enumerate(spell.step_groups):
        #     target = getattr(group, "relative_distance", None)
        #     if target is None:
        #         continue

        #     actual = metrics.group_distance[gi] / total

        #     tol_ratio = spell.group_distance_rel_tol  # e.g. 0.25 for ±25%
        #     band = abs(target) * tol_ratio

        #     lower = max(0.0, target - band)
        #     upper = min(1.0, target + band)

        #     if not (lower <= actual <= upper):
        #         return False

        # return True
