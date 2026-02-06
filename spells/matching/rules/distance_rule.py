from gamevolt_logging import get_logger

from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext

logger = get_logger()


class DistanceRule(SpellRule):
    def validate(self, ctx: SpellMatchContext) -> bool:
        s = ctx.spell
        m = ctx.metrics

        dist = m.total_distance + m.absorbed_distance

        logger.info(f"min: {s.min_total_distance} | dist: {dist} | max: {s.max_total_distance} ")

        if s.min_total_distance is not None and dist < s.min_total_distance:
            return False

        if s.max_total_distance is not None and dist > s.max_total_distance:
            return False

        return True
