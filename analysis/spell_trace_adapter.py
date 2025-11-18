# analysis/spell_trace_adapter.py
from __future__ import annotations

from typing import Iterable

from analysis.spell_trace_api import SpellTrace
from analysis.spell_tracer import SpellAttemptTrace, TraceReason
from motion.gesture.gesture_segment import GestureSegment
from spells.spell_definition import SpellDefinition
from spells.spell_step import SpellStep


class SpellTraceAdapter(SpellTrace):
    def __init__(self, attempt: SpellAttemptTrace):
        self.a = attempt

    def attempt_start(self, spell: SpellDefinition, compressed: Iterable[GestureSegment]) -> None:
        self.a.spell_id = spell.id
        self.a.spell_name = spell.name
        # key_count is set by the matcher (so it can decide required vs all)
        self.a.log(t_ms=self._last_ts(compressed), reason=TraceReason.ATTEMPT_START, msg=f"compressed={sum(1 for _ in compressed)}")

    def compressed_summary(self, compressed: Iterable[GestureSegment]) -> None:
        items = list(compressed)
        s = " | ".join(f"{i}:{seg.direction_type.name}[{seg.duration_s:.2f}s]" for i, seg in enumerate(items))
        self.a.log(t_ms=self._last_ts(items), reason=TraceReason.COMPRESSED_INPUT, msg=s)

    def idle_tolerated(self, seg, idx):
        self.a.log(t_ms=seg.end_ts_ms, reason=TraceReason.IDLE_TOLERATED, segment=seg, segment_idx=idx)

    def idle_too_long_reset(self, seg, idx, max_gap_s):
        self.a.log(
            t_ms=seg.end_ts_ms, reason=TraceReason.IDLE_TOO_LONG_RESET, segment=seg, segment_idx=idx, msg=f"max_gap={max_gap_s:.2f}s"
        )

    def window_exceeded_reset(self, seg, idx, window_s, limit_s):
        self.a.log(
            t_ms=seg.end_ts_ms,
            reason=TraceReason.WINDOW_EXCEEDED_RESET,
            segment=seg,
            segment_idx=idx,
            msg=f"window={self._fmt(window_s)} > {self._fmt(limit_s)}",
        )

    def step_match(self, seg, idx, step: SpellStep, step_idx: int):
        self.a.log(t_ms=seg.end_ts_ms, reason=TraceReason.STEP_MATCH, segment=seg, segment_idx=idx, step=step, step_idx=step_idx)
        self.a.matched_keys += 1

    def step_fail_dir(self, seg, idx, step, step_idx):
        self.a.log(t_ms=seg.end_ts_ms, reason=TraceReason.STEP_FAIL_DIR, segment=seg, segment_idx=idx, step=step, step_idx=step_idx)

    def step_fail_dur(self, seg, idx, step, step_idx):
        self.a.log(
            t_ms=seg.end_ts_ms,
            reason=TraceReason.STEP_FAIL_DUR,
            segment=seg,
            segment_idx=idx,
            step=step,
            step_idx=step_idx,
            msg=f"{seg.duration_s:.2f} < {step.min_duration_s:.2f}",
        )

    def segment_ignored(self, seg, idx, step, step_idx):
        self.a.log(t_ms=seg.end_ts_ms, reason=TraceReason.SEGMENT_IGNORED, segment=seg, segment_idx=idx, step=step, step_idx=step_idx)

    def complete(self, end_ts_ms: int) -> None:
        self.a.success = True
        self.a.end_ts_ms = end_ts_ms
        self.a.log(t_ms=end_ts_ms, reason=TraceReason.COMPLETE)

    def attempt_end(self) -> None:
        self.a.log(t_ms=self.a.end_ts_ms or 0, reason=TraceReason.ATTEMPT_END)

    @staticmethod
    def _last_ts(items: Iterable[GestureSegment]) -> int:
        last = None
        for last in items:
            pass
        return getattr(last, "end_ts_ms", 0) if last is not None else 0

    @staticmethod
    def _fmt(x: float) -> str:
        return f"{x:.2f}s"
