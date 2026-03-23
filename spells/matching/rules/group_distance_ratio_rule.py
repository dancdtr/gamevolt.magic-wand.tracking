from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class GroupDistanceRatioRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        m = ctx.metrics

        # Use effective total distance (scorable + absorbed jitter)
        total = max(m.total_distance, spell.group_distance_min_total)

        for gi, group in enumerate(spell.step_groups):
            target = getattr(group, "relative_distance", None)
            if target is None:
                continue

            # Use effective group distance (scorable + absorbed jitter attributed to this group)
            group_dist = m.group_distance[gi] + m.group_absorbed_distance[gi]
            actual = group_dist / total

            band = abs(target) * spell.group_distance_rel_tol
            lower = max(0.0, target - band)
            upper = min(1.0, target + band)

            if not (lower <= actual <= upper):
                return False

        return True
