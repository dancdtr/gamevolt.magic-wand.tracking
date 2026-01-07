# spells/spell_matcher_base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from logging import Logger

from gamevolt.events.event import Event
from motion.gesture.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_step import SpellStep


class SpellMatcherBase(ABC):
    def __init__(self, logger: Logger):
        self._logger = logger

        self.matched: Event[Callable[[SpellMatch], None]] = Event()

    @property
    @abstractmethod
    def spell_definitions(self) -> list[SpellDefinition]: ...

    # ----- public entry point -----
    def try_match(self, wand_id: str, wand_name: str, history: Sequence[GestureSegment]) -> bool:
        if not history:
            return False
        compressed = self._compress(history)  # oldest → newest

        for spell in self.spell_definitions:
            match = self._match_spell(wand_id, wand_name, spell, compressed)
            if match:
                self._logger.info(
                    f"'{wand_name}' ({wand_id}) cast {match.spell_name}! ✨✨" f"{match.accuracy_score * 100:.1f}% ({match.duration_s:.3f})"
                )
                self.matched.invoke(match)
                return True

        return False

    # ----- subclass must implement -----
    def _match_spell(self, wand_id: str, wand_name: str, spell: SpellDefinition, compressed: Sequence[GestureSegment]) -> SpellMatch | None:
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
