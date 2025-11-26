# analysis/spell_trace_api.py
from __future__ import annotations

from typing import Iterable, Protocol

from motion.gesture.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep


class SpellTrace(Protocol):
    # lifecycle
    def attempt_start(self, spell: SpellDefinition, compressed: Iterable[GestureSegment]) -> None: ...
    def attempt_end(self) -> None: ...
    def complete(self, end_ts_ms: int) -> None: ...

    # helpful breadcrumbs
    def compressed_summary(self, compressed: Iterable[GestureSegment]) -> None: ...
    def idle_tolerated(self, seg: GestureSegment, idx: int) -> None: ...
    def idle_too_long_reset(self, seg: GestureSegment, idx: int, max_gap_s: float) -> None: ...
    def window_exceeded_reset(self, seg: GestureSegment, idx: int, window_s: float, limit_s: float) -> None: ...
    def step_match(self, seg: GestureSegment, idx: int, step: SpellStep, step_idx: int) -> None: ...
    def step_fail_dir(self, seg: GestureSegment, idx: int, step: SpellStep, step_idx: int) -> None: ...
    def step_fail_dur(self, seg: GestureSegment, idx: int, step: SpellStep, step_idx: int) -> None: ...
    def segment_ignored(self, seg: GestureSegment, idx: int, step: SpellStep, step_idx: int) -> None: ...


class NullSpellTrace:
    # all methods no-op
    def attempt_start(self, *_args, **_kw):
        pass

    def attempt_end(self, *_args, **_kw):
        pass

    def complete(self, *_args, **_kw):
        pass

    def compressed_summary(self, *_args, **_kw):
        pass

    def idle_tolerated(self, *_args, **_kw):
        pass

    def idle_too_long_reset(self, *_args, **_kw):
        pass

    def window_exceeded_reset(self, *_args, **_kw):
        pass

    def step_match(self, *_args, **_kw):
        pass

    def step_fail_dir(self, *_args, **_kw):
        pass

    def step_fail_dur(self, *_args, **_kw):
        pass

    def segment_ignored(self, *_args, **_kw):
        pass
