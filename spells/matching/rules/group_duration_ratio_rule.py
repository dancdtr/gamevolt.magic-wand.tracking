from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class GroupDurationRatioRule(SpellRule):
    """
    Same idea as GroupDistanceRatioRule, but using per-group duration instead.
    """

    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        metrics = ctx.metrics

        total = max(metrics.total_duration_s, spell.group_duration_min_total_s)

        for gi, group in enumerate(spell.step_groups):
            target = getattr(group, "relative_duration", None)
            if target is None:
                continue

            actual = metrics.group_duration_s[gi] / total

            tol_ratio = spell.group_duration_rel_tol  # e.g. 0.25 for ±25%
            band = abs(target) * tol_ratio

            lower = max(0.0, target - band)
            upper = min(1.0, target + band)

            if not (lower <= actual <= upper):
                return False

        return True
