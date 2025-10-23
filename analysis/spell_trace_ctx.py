# analysis/spell_trace_ctx.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable

from analysis.spell_trace_api import NullSpellTrace, SpellTrace
from motion.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition


@contextmanager
def spell_trace_ctx(spell: SpellDefinition, compressed: Iterable[GestureSegment], trace: SpellTrace | None):
    T: SpellTrace = trace or NullSpellTrace()
    T.attempt_start(spell, compressed)
    try:
        yield T
    finally:
        T.attempt_end()
