# spells/spell_matcher_base.py
from __future__ import annotations

from collections.abc import Callable, Sequence
from logging import Logger

from gamevolt.events.event import Event
from motion.gesture.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_step import SpellStep


class SpellMatcherBase:
    def __init__(self, logger: Logger, spells: Sequence[SpellDefinition]):
        self._logger = logger
        self._spells = list(spells)

        self.matched: Event[Callable[[SpellMatch], None]] = Event()

    # ----- public entry point -----
    def try_match(self, history: Sequence[GestureSegment]) -> None:
        if not history:
            return
        compressed = self._compress(history)  # oldest → newest

        for spell in self._spells:
            match = self._match_spell(spell, compressed)
            if match:
                self.matched.invoke(match)
                break

    # ----- subclass must implement -----
    def _match_spell(self, spell: SpellDefinition, compressed: Sequence[GestureSegment]) -> SpellMatch | None:
        raise NotImplementedError

    # ----- shared helpers -----
    def _key_steps(self, spell: SpellDefinition) -> list[SpellStep]:
        """Required steps define the key sequence; if none required, use all steps."""
        req = [st for grp in spell.step_groups for st in grp.steps if getattr(st, "required", False)]
        return req if req else [st for grp in spell.step_groups for st in grp.steps]

    def _compress(self, segments: Sequence[GestureSegment]) -> list[GestureSegment]:
        """
        Merge consecutive identical directions (including NONE is kept separate),
        summing duration & path_length; recompute mean_speed accordingly.
        """
        if not segments:
            return []
        out: list[GestureSegment] = []
        cur = segments[0]
        for seg in segments[1:]:
            if seg.direction_type == cur.direction_type:
                total_dur = cur.duration_s + seg.duration_s
                total_path = cur.path_length + seg.path_length
                cur = type(cur)(
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
