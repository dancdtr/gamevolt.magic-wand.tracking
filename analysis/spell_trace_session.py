# analysis/spell_trace_session.py
from __future__ import annotations

from dataclasses import dataclass
from pprint import pp
from typing import Callable, Sequence

from gamevolt_logging import get_logger

from analysis.spell_trace_api import NullSpellTrace, SpellTrace
from motion.direction_type import DirectionType
from motion.gesture_segment import GestureSegment
from motion.motion_type import MotionType
from spells.spell_match import SpellMatch
from spells.spell_matcher_manager import SpellMatcherManager

logger = get_logger()


@dataclass
class SpellTraceSessionConfig:
    natural_break_s: float = 0.9  # idle NONE ≥ this ends the attempt
    clear_history_on_flush: bool = True
    label_prefix: str = "TRACE"


class SpellTraceSessionManager:
    """
    Owns a 'current attempt' tracer. Starts on MOVING, always passes a valid tracer
    (real or NullSpellTrace) to matcher.try_match(), and flushes on match or natural break.
    """

    def __init__(self, trace_factory: Callable[[], SpellTrace], config: SpellTraceSessionConfig | None = None) -> None:
        self._trace_factory = trace_factory
        self._cfg = config or SpellTraceSessionConfig()
        self._enabled: bool = True

        # Always hold a tracer (Null until an attempt starts)
        self._trace: SpellTrace = NullSpellTrace()
        self._active: bool = False  # whether we're inside an active attempt

    # --- control ---
    def set_enabled(self, enabled: bool) -> None:
        if not enabled and self._active:
            self.flush("tracing-off")
        self._enabled = enabled
        if not enabled:
            # ensure we’re back to a clean Null tracer
            self._trace = NullSpellTrace()
            self._active = False

    def toggle(self) -> None:
        self.set_enabled(not self._enabled)
        logger.info(f"Tracing {'ENABLED' if self._enabled else 'DISABLED'}")

    # --- hooks you call from your app ---
    def on_motion_changed(self, mode: MotionType) -> None:
        # Start a new attempt on real motion
        if self._enabled and mode == MotionType.MOVING and not self._active:
            self._trace = self._trace_factory()
            self._active = True

    def on_segment(
        self,
        segment: GestureSegment,
        history_tail: Sequence[GestureSegment],
        matcher_manager: SpellMatcherManager,
        *,
        history_clear_fn: Callable[[], None] | None = None,
    ) -> None:
        """
        Feed the tracer into matching each time a segment completes.
        If the segment is a long NONE, flush (natural break).
        """
        matcher_manager.try_match(history_tail, self._trace)

        # Natural break: end attempt after a long NONE
        if segment.direction_type == DirectionType.NONE and segment.duration_s >= self._cfg.natural_break_s:
            self.flush("break")
            if self._cfg.clear_history_on_flush and history_clear_fn:
                history_clear_fn()

    def on_match(self, match: SpellMatch, *, history_clear_fn: Callable[[], None] | None = None) -> None:
        # Successful attempt ends the trace
        self.flush("match")
        if self._cfg.clear_history_on_flush and history_clear_fn:
            history_clear_fn()

    def on_difficulty_changed(self) -> None:
        # Changing models? close any ongoing attempt
        self.flush("difficulty-changed")

    # --- internals ---
    def flush(self, reason: str = "") -> None:
        if not self._active:
            return
        # If using SpellTraceAdapter, it has .a.pretty(); otherwise rely on tracer’s own logging.
        attempt_obj = getattr(self._trace, "a", None)
        if attempt_obj is not None and hasattr(attempt_obj, "pretty"):
            logger.debug(f"[{self._cfg.label_prefix} {reason}] \n{attempt_obj.pretty()}")
        # Reset to Null tracer
        self._trace = NullSpellTrace()
        self._active = False

    # Expose the current tracer (always non-null); handy if you need to inspect it
    def current(self) -> SpellTrace:
        return self._trace
