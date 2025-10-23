# analysis/spell_tracer.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from motion.direction_type import DirectionType
from motion.gesture_segment import GestureSegment
from spells.spell_step import SpellStep


class TraceReason(Enum):
    ATTEMPT_START = auto()
    COMPRESSED_INPUT = auto()
    IDLE_TOLERATED = auto()
    IDLE_TOO_LONG_RESET = auto()
    WINDOW_EXCEEDED_RESET = auto()
    STEP_MATCH = auto()
    STEP_FAIL_DIR = auto()
    STEP_FAIL_DUR = auto()
    SEGMENT_IGNORED = auto()
    COMPLETE = auto()
    ATTEMPT_END = auto()


@dataclass
class SegSnap:
    index: int
    direction: DirectionType
    duration: float
    path: float
    start_ms: int
    end_ms: int


@dataclass
class StepSnap:
    index: int
    allowed: frozenset[DirectionType]
    min_duration: float


@dataclass
class TraceEvent:
    t_ms: int
    reason: TraceReason
    segment: SegSnap | None = None
    step: StepSnap | None = None
    msg: str = ""


@dataclass
class SpellAttemptTrace:
    spell_id: str
    spell_name: str
    key_count: int
    events: list[TraceEvent] = field(default_factory=list)
    matched_keys: int = 0
    success: bool = False
    start_ts_ms: int | None = None
    end_ts_ms: int | None = None

    def log(
        self,
        *,
        t_ms: int,
        reason: TraceReason,
        segment: GestureSegment | None = None,
        segment_idx: int | None = None,
        step: SpellStep | None = None,
        step_idx: int | None = None,
        msg: str = "",
    ) -> None:
        snap_seg = None
        if segment is not None and segment_idx is not None:
            snap_seg = SegSnap(
                segment_idx, segment.direction_type, segment.duration_s, segment.path_length, segment.start_ts_ms, segment.end_ts_ms
            )
        snap_step = None
        if step is not None and step_idx is not None:
            snap_step = StepSnap(step_idx, step.allowed, step.min_duration_s)
        self.events.append(TraceEvent(t_ms=t_ms, reason=reason, segment=snap_seg, step=snap_step, msg=msg))

    def pretty(self) -> str:
        lines = [
            f"[{self.spell_id}] {self.spell_name} keys={self.key_count} matched={self.matched_keys} "
            f"success={self.success} window={None if self.start_ts_ms is None or self.end_ts_ms is None else (self.end_ts_ms - self.start_ts_ms)}ms"
        ]
        for e in self.events:
            seg = (
                f" seg#{e.segment.index} {e.segment.direction.name} dur={e.segment.duration:.3f}s path={e.segment.path:.3f}"
                if e.segment
                else ""
            )
            step = (
                f" next_step#{e.step.index} allowed={[d.name for d in (e.step.allowed if e.step else [])]} min_dur={e.step.min_duration:.2f}"
                if e.step
                else ""
            )
            lines.append(f"  {e.reason.name:<22} t={e.t_ms} {seg} {step} {e.msg}")
        return "\n".join(lines)
