from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class GroupDistanceRatioRule(SpellRule):
    """
    Checks that each step_group's share of total distance is within a tolerance
    of its configured relative_distance.
    """

    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        metrics = ctx.metrics

        total = max(metrics.total_distance, spell.group_distance_min_total)

        for gi, group in enumerate(spell.step_groups):
            target = getattr(group, "relative_distance", None)
            if target is None:
                continue

            actual = metrics.group_distance[gi] / total
            if abs(actual - target) > spell.group_distance_rel_tol:
                return False

        return True
