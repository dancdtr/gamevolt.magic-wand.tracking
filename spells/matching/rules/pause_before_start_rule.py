from __future__ import annotations

from motion.direction.direction_type import DirectionType
from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class PauseBeforeStartRule(SpellRule):
    """
    Enforces a minimum pause immediately *before* the spell window.

    Logic:
      - Walk backward from window_start_index - 1.
      - While segments look "paused" (NONE or low mean_speed), accumulate duration.
      - If accumulated >= spell.min_pre_pause_s, pass; otherwise fail.

    If there are no earlier segments, we treat this as pass (start of stream).
    """

    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        segs = ctx.segments

        min_pre = spell.min_pre_pause_s
        if min_pre is None or min_pre <= 0.0:
            return True  # rule disabled

        start_idx = ctx.window_start_index
        if start_idx <= 0:
            # No earlier segments → treat as "paused before start"
            return True

        remaining = min_pre
        thresh = spell.pause_speed_threshold

        j = start_idx - 1
        while j >= 0 and remaining > 0.0:
            seg = segs[j]

            is_pause = seg.direction_type == DirectionType.NONE or seg.mean_speed <= thresh

            if not is_pause:
                # As soon as we hit motion, we stop counting pause
                break

            remaining -= seg.duration_s
            j -= 1

        return remaining <= 0.0
