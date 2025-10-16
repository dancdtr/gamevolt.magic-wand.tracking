# spell_matcher.py
from typing import Callable, List, Sequence

from gamevolt.events.event import Event
from motion.direction_type import DirectionType
from motion.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_matcher_base import SpellMatcherBase
from spells.spell_step import SpellStep

_RELATIVE_TOL = 0.15
_MIN_TOTAL_DIST = 1e-6
_CHECK_DISTANCE = False


class SpellMatcher(SpellMatcherBase):
    def __init__(self, spells: Sequence[SpellDefinition]):
        self._spells = list(spells)
        self._matched: Event[Callable[[SpellMatch], None]] = Event()

    @property
    def matched(self) -> Event[Callable[[SpellMatch], None]]:
        return self._matched

    def try_match(self, history: Sequence[GestureSegment]) -> None:
        if not history:
            return
        compressed = self._compress(history)  # oldest → newest
        for spell in self._spells:
            m = self._match_spell(spell, compressed)
            if m:
                self.matched.invoke(m)
                break

    def _compress(self, segments: Sequence[GestureSegment]) -> list[GestureSegment]:
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
                    path_length=total_path,  # ← carry distance
                )
            else:
                out.append(cur)
                cur = seg
        out.append(cur)
        return out

    def _match_spell(self, spell: SpellDefinition, segments: Sequence[GestureSegment]) -> SpellMatch | None:
        if not segments:
            return None
        # Flatten once per spell attempt
        flat_steps, group_idx_of_step = self._flatten_with_group_map(spell)

        # try windows starting at each index from newest back
        for start_idx in range(len(segments) - 1, -1, -1):
            m = self._match_from_index(spell, flat_steps, group_idx_of_step, segments, start_idx)
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

        steps = list(reversed(flat_steps))
        step_to_group = list(reversed(group_idx_of_step))

        step_idx = 0
        used = 0
        start_ts = None
        end_ts = None
        total_duration = 0.0

        group_distance = [0.0 for _ in spell.step_groups]
        total_distance = 0.0

        i = i_start
        while i >= 0 and step_idx < len(steps):
            seg = segs[i]

            # ✅ ensure timestamps are captured
            if start_ts is None:
                start_ts = seg.start_ts_ms
            end_ts = seg.end_ts_ms

            step = steps[step_idx]
            dt = seg.duration_s
            # dist = _segment_distance(seg)
            dist = seg.path_length

            # tolerate short NONE gaps (no distance added)
            if seg.direction_type == DirectionType.NONE:
                if dt <= spell.max_idle_gap_s:
                    total_duration += dt
                    i -= 1
                    continue
                else:
                    return None

            dir_ok = seg.direction_type in step.allowed
            dur_ok = dt >= step.min_duration_s

            if dir_ok and dur_ok:
                total_duration += dt
                total_distance += dist

                gi = step_to_group[step_idx]
                group_distance[gi] += dist

                used += 1
                step_idx += 1
                i -= 1

                if spell.max_total_duration_s is not None and total_duration > spell.max_total_duration_s:
                    return None
                continue

            if step.required:
                return None
            else:
                step_idx += 1
                continue

        if step_idx == len(steps) and used >= spell.min_spell_steps and start_ts is not None and end_ts is not None:
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
