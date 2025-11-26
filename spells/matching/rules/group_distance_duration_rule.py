from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class GroupDistanceRatioRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        metrics = ctx.metrics

        total = max(metrics.total_distance, spell.group_distance_min_total)

        for gi, group in enumerate(spell.step_groups):
            target = getattr(group, "relative_distance", None)
            if target is None:
                continue

            actual = metrics.group_distance[gi] / total

            tol_ratio = spell.group_distance_rel_tol
            band = abs(target) * tol_ratio

            lower = max(0.0, target - band)
            upper = min(1.0, target + band)

            if not (lower <= actual <= upper):
                return False

        return True
