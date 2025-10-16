# spells/easy_spell_matcher.py
from __future__ import annotations

from typing import Callable, List, Sequence

from gamevolt.events.event import Event
from motion.direction_type import DirectionType
from motion.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_matcher_base import SpellMatcherBase
from spells.spell_step import SpellStep


class EasySpellMatcher(SpellMatcherBase):
    """
    Forgiving subsequence matcher:
    - Only 'key' steps (required=True) must appear in order.
      If no steps are marked required, all steps are treated as keys.
    - Anything else between keys is tolerated (diagonals, repeats, short NONE),
      subject to max_idle_gap_s and max_total_duration_s.
    - Respects spell.min_spell_steps (counting matched key-steps).
    """

    def __init__(self, spells: Sequence[SpellDefinition]):
        self._spells = list(spells)
        self._matched: Event[Callable[[SpellMatch], None]] = Event()

    @property
    def matched(self) -> Event[Callable[[SpellMatch], None]]:
        return self._matched

    # ---------- public ----------
    def try_match(self, history: Sequence[GestureSegment]) -> None:
        if not history:
            return
        compressed = self._compress(history)  # oldest → newest
        for spell in self._spells:
            key_steps = self._key_steps(spell)
            if not key_steps:
                continue
            m = self._match_subsequence(spell, key_steps, compressed)
            if m:
                self.matched.invoke(m)
                break

    # ---------- internals ----------
    def _key_steps(self, spell: SpellDefinition) -> list[SpellStep]:
        # Only required steps act as the "must-hit" subsequence; fallback to all.
        required = [st for grp in spell.step_groups for st in grp.steps if getattr(st, "required", False)]
        return required if required else [st for grp in spell.step_groups for st in grp.steps]

    def _compress(self, segments: Sequence[GestureSegment]) -> list[GestureSegment]:
        """
        Merge consecutive segments of the same direction, summing duration/path.
        Keep NONE as its own segments to enforce idle gap.
        """
        if not segments:
            return []
        out: List[GestureSegment] = []
        cur = segments[0]
        for seg in segments[1:]:
            if seg.direction_type == cur.direction_type:
                total_dur = cur.duration_s + seg.duration_s
                total_path = cur.path_length + seg.path_length
                cur = GestureSegment(
                    start_ts_ms=cur.start_ts_ms,
                    end_ts_ms=seg.end_ts_ms,
                    duration_s=total_dur,
                    sample_count=cur.sample_count + seg.sample_count,
                    direction_type=cur.direction_type,
                    avg_vec_x=0.0,
                    avg_vec_y=0.0,
                    net_dx=cur.net_dx + seg.net_dx,
                    net_dy=cur.net_dy + seg.net_dy,
                    mean_speed=(total_path / total_dur) if total_dur > 0 else 0.0,
                    path_length=total_path,
                )
            else:
                out.append(cur)
                cur = seg
        out.append(cur)
        return out

    def _match_subsequence(
        self,
        spell: SpellDefinition,
        key_steps: Sequence[SpellStep],
        segs: Sequence[GestureSegment],
    ) -> SpellMatch | None:
        """
        Greedy oldest→newest scan:
          - Advance only when a segment satisfies the next key step.
          - Ignore diagonals/other movement between keys.
          - Reset on long NONE (idle > max_idle_gap_s).
          - Enforce overall max_total_duration_s, but allow restart from the current seg.
        """
        i_key = 0
        matched_keys = 0
        started = False
        start_ts = None
        end_ts = None

        for seg in segs:
            # Idle handling
            if seg.direction_type == DirectionType.NONE:
                if seg.duration_s > (spell.max_idle_gap_s or 0.0):
                    # break the run
                    i_key = 0
                    matched_keys = 0
                    started = False
                    start_ts = None
                continue

            # Maybe (re)start on this segment
            if not started:
                if self._seg_satisfies_step(seg, key_steps[0]):
                    started = True
                    start_ts = seg.start_ts_ms
                    end_ts = seg.end_ts_ms
                    matched_keys = 1
                    i_key = 1
                    if self._complete(spell, matched_keys, len(key_steps)):
                        return self._mk_match(spell, start_ts, end_ts, matched_keys, len(key_steps))
                # else ignore and keep scanning
                continue

            # Window check (overall)
            if spell.max_total_duration_s is not None and start_ts is not None:
                window_s = (seg.end_ts_ms - start_ts) / 1000.0
                if window_s > spell.max_total_duration_s:
                    # restart attempt at this seg
                    i_key = 0
                    matched_keys = 0
                    started = False
                    start_ts = None
                    # allow this same seg to seed a fresh start
                    if self._seg_satisfies_step(seg, key_steps[0]):
                        started = True
                        start_ts = seg.start_ts_ms
                        end_ts = seg.end_ts_ms
                        matched_keys = 1
                        i_key = 1
                        if self._complete(spell, matched_keys, len(key_steps)):
                            return self._mk_match(spell, start_ts, end_ts, matched_keys, len(key_steps))
                    continue

            # Progress the key sequence if this segment satisfies the next key
            if self._seg_satisfies_step(seg, key_steps[i_key]):
                matched_keys += 1
                i_key += 1
                end_ts = seg.end_ts_ms
                if self._complete(spell, matched_keys, len(key_steps)):
                    return self._mk_match(spell, start_ts or seg.start_ts_ms, end_ts, matched_keys, len(key_steps))
            # else: ignore and keep scanning

        return None

    @staticmethod
    def _seg_satisfies_step(seg: GestureSegment, step: SpellStep) -> bool:
        # Direction must be in allowed; honour per-step min_duration if set.
        if seg.direction_type not in step.allowed:
            return False
        if step.min_duration_s > 0.0 and seg.duration_s < step.min_duration_s:
            return False
        return True

    @staticmethod
    def _complete(spell: SpellDefinition, matched_keys: int, total_keys: int) -> bool:
        # Finish when we meet min_spell_steps (defaults to all keys if larger)
        need = min(getattr(spell, "min_spell_steps", total_keys) or total_keys, total_keys)
        return matched_keys >= need

    @staticmethod
    def _mk_match(spell: SpellDefinition, start_ts: int, end_ts: int, used: int, total_keys: int) -> SpellMatch:
        return SpellMatch(
            spell_id=spell.id,
            spell_name=spell.name,
            start_ts_ms=start_ts,
            end_ts_ms=end_ts,
            duration_s=(end_ts - start_ts) / 1000.0,
            segments_used=used,
            total_segments=total_keys,
        )
