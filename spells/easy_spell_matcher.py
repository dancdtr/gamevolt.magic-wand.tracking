# spells/easy_spell_matcher.py
from __future__ import annotations

from typing import Optional, Sequence

from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_matcher_base import SpellMatcherBase
from spells.spell_step import SpellStep


class EasySpellMatcher(SpellMatcherBase):
    """
    Forgiving subsequence: only key steps (required=True, else all) must
    appear in order; anything else between is tolerated, bounded by
    max_idle_gap_s and max_total_duration_s.
    """

    def _match_spell(self, spell: SpellDefinition, segs: Sequence[GestureSegment]) -> Optional[SpellMatch]:

        key_steps = self._key_steps(spell)
        if not key_steps:
            return None

        i_key = 0
        matched_keys = 0
        started = False
        start_ts = None
        end_ts = None

        for idx, seg in enumerate(segs):
            # idle handling
            if seg.direction_type == DirectionType.NONE:
                if seg.duration_s > (spell.max_idle_gap_s or 0.0):
                    i_key = matched_keys = 0
                    started = False
                    start_ts = None

            # maybe start on this segment
            if not started:
                if self._seg_satisfies_step(seg, key_steps[0]):
                    started = True
                    start_ts = seg.start_ts_ms
                    end_ts = seg.end_ts_ms
                    matched_keys = 1
                    i_key = 1
                    if self._complete(spell, matched_keys, len(key_steps)):
                        return self._mk(spell, start_ts, end_ts, matched_keys, len(key_steps))

            # overall time window
            if spell.max_total_duration is not None and start_ts is not None:
                window_s = (seg.end_ts_ms - start_ts) / 1000.0
                if window_s > spell.max_total_duration:
                    i_key = matched_keys = 0
                    started = False
                    start_ts = None
                    # allow restart on this seg
                    if self._seg_satisfies_step(seg, key_steps[0]):
                        started = True
                        start_ts = seg.start_ts_ms
                        end_ts = seg.end_ts_ms
                        matched_keys = 1
                        i_key = 1
                    continue

            # advance key when satisfied
            next_step = key_steps[i_key]
            if self._seg_satisfies_step(seg, next_step):
                matched_keys += 1
                i_key += 1
                end_ts = seg.end_ts_ms
                if self._complete(spell, matched_keys, len(key_steps)):
                    return self._mk(spell, start_ts or seg.start_ts_ms, end_ts, matched_keys, len(key_steps))

        return None

    # --- tiny helpers for this matcher ---
    @staticmethod
    def _seg_satisfies_step(seg: GestureSegment, step: SpellStep) -> bool:
        return (seg.direction_type in step.allowed) and (step.min_duration_s <= 0.0 or seg.duration_s >= step.min_duration_s)

    @staticmethod
    def _complete(spell: SpellDefinition, matched_keys: int, total_keys: int) -> bool:
        need = min(getattr(spell, "min_spell_steps", total_keys) or total_keys, total_keys)
        return matched_keys >= need

    @staticmethod
    def _mk(spell: SpellDefinition, start_ts: int, end_ts: int, used: int, total: int) -> SpellMatch:
        return SpellMatch(
            spell_id=spell.id,
            spell_name=spell.name,
            start_ts_ms=start_ts,
            end_ts_ms=end_ts,
            duration_s=(end_ts - start_ts) / 1000.0,
            segments_used=used,
            total_segments=total,
        )
