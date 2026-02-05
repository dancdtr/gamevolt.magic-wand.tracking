from __future__ import annotations

from motion.direction.direction_type import DirectionType
from spells.matching.rules.spell_rule import SpellRule
from spells.matching.spell_match_context import SpellMatchContext


class PauseAtEndRule(SpellRule):
    """
    Enforces a minimum pause immediately *after* the spell window.

    Logic:
      - Walk forward from window_end_index + 1.
      - While segments look "paused" (NONE or low mean_speed), accumulate duration.
      - If accumulated >= spell.min_post_pause_s, pass; otherwise fail.

    If there are no later segments, we treat this as pass (end of stream).
    """

    def validate(self, ctx: SpellMatchContext) -> bool:
        spell = ctx.spell
        segs = ctx.segments

        min_post = spell.min_post_pause_s
        if min_post is None or min_post <= 0.0:
            return True  # rule disabled

        end_idx = ctx.window_end_index
        if end_idx >= len(segs) - 1:
            # No later segments → treat as "paused after end"
            return True

        remaining = min_post
        thresh = spell.pause_speed_threshold

        j = end_idx + 1
        while j < len(segs) and remaining > 0.0:
            seg = segs[j]

            is_pause = seg.direction_type == DirectionType.UNKNOWN or seg.mean_speed <= thresh

            if not is_pause:
                break

            remaining -= seg.duration_s
            j += 1

        return remaining <= 0.0
