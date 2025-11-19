from __future__ import annotations

from typing import Sequence

from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_matcher_base import SpellMatcherBase
from spells.spell_step import SpellStep

_RELATIVE_TOL = 0.15
_MIN_TOTAL_DIST = 1e-6
_CHECK_DISTANCE = False


class SpellMatcher(SpellMatcherBase):
    def _match_spell(self, spell: SpellDefinition, compressed: Sequence[GestureSegment]) -> SpellMatch | None:
        if not compressed:
            return None

        flat_steps, group_idx_of_step = self._flatten_with_group_map(spell)

        # try windows starting at each index from newest back
        for start_idx in range(len(compressed) - 1, -1, -1):
            m = self._match_from_index(spell, flat_steps, group_idx_of_step, compressed, start_idx)
            if m:
                return m
        return None

    def _flatten_with_group_map(self, spell: SpellDefinition) -> tuple[list[SpellStep], list[int]]:
        flat: list[SpellStep] = []
        group_map: list[int] = []
        for gi, grp in enumerate(spell.step_groups):
            for st in grp.steps:
                flat.append(st)
                group_map.append(gi)
        return flat, group_map

    def _match_from_index(
        self,
        spell: SpellDefinition,
        flat_steps: Sequence[SpellStep],
        group_idx_of_step: Sequence[int],
        segs: Sequence[GestureSegment],
        i_start: int,
    ) -> SpellMatch | None:

        # reversed because we walk newest→oldest
        steps = list(reversed(flat_steps))
        step_to_group = list(reversed(group_idx_of_step))

        step_idx = 0
        used = 0
        start_ts: int | None = None
        end_ts: int | None = None
        total_duration = 0.0

        group_distance = [0.0 for _ in spell.step_groups]
        total_distance = 0.0

        # total time spent in "filler" segments (any direction)
        filler_duration = 0.0

        def would_exceed_total_duration(extra: float) -> bool:
            if spell.max_total_duration is None:
                return False
            return (total_duration + extra) > spell.max_total_duration

        i = i_start
        while i >= 0 and step_idx < len(steps):
            seg = segs[i]

            # capture time window endpoints (chronologically correct)
            if start_ts is None:
                start_ts = seg.start_ts_ms
            end_ts = seg.end_ts_ms

            dt = seg.duration_s
            dist = seg.path_length
            step = steps[step_idx]

            # helper: try to treat this segment as filler (any direction)
            def try_consume_as_filler() -> bool:
                nonlocal filler_duration, total_duration, i
                # (optional) hard per-seg limit for NONE gaps
                if seg.direction_type == DirectionType.NONE and dt > spell.max_idle_gap_s:
                    return False

                # respect overall filler budget
                if filler_duration + dt > spell.max_filler_duration_s:
                    return False

                # respect overall spell window
                if would_exceed_total_duration(dt):
                    return False

                filler_duration += dt
                total_duration += dt
                i -= 1
                return True

            # If it's NONE, we *only* consider it as filler, never as a step
            if seg.direction_type == DirectionType.NONE:
                if not try_consume_as_filler():
                    return None
                continue

            # check this segment against the current step
            dir_ok = seg.direction_type in step.allowed
            dur_ok = dt >= step.min_duration_s

            if dir_ok and dur_ok:
                # matched a step
                if would_exceed_total_duration(dt):
                    return None

                total_duration += dt
                total_distance += dist

                gi = step_to_group[step_idx]
                group_distance[gi] += dist

                used += 1
                step_idx += 1
                i -= 1
                continue

            # At this point: seg does NOT satisfy the current step

            # First, see if we can "forgive" it as filler
            if try_consume_as_filler():
                # still aiming to match the same step_idx on the next iteration
                continue

            # Can't treat it as filler; if the step is required, the spell fails.
            if step.required:
                return None

            # Optional step: skip it and try to match this same seg against the next step
            step_idx += 1
            # NOTE: we intentionally do NOT decrement i here so we
            # re-check this same segment against the next step.

        # end condition
        if step_idx == len(steps) and used >= spell.min_spell_steps and start_ts is not None and end_ts is not None:
            # optional distance-ratio check
            if _CHECK_DISTANCE:
                denom = max(total_distance, _MIN_TOTAL_DIST)
                for gi, grp in enumerate(spell.step_groups):
                    target = getattr(grp, "relative_distance", None)
                    if target is None:
                        continue
                    actual = group_distance[gi] / denom
                    if abs(actual - target) > _RELATIVE_TOL:
                        return None

            return SpellMatch(
                spell_id=spell.id,
                spell_name=spell.name,
                start_ts_ms=start_ts,
                end_ts_ms=end_ts,
                duration_s=total_duration,
                segments_used=used,
                total_segments=len(flat_steps),
            )

        return None
