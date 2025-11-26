# analysis/spell_trace_session.py
from __future__ import annotations

from logging import Logger
from typing import Callable, Sequence

from analysis.spell_trace_adapter_factory import SpellTraceAdapterFactory
from analysis.spell_trace_api import NullSpellTrace, SpellTrace
from analysis.spell_trace_session_settings import SpellTraceSessionSettings
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from motion.motion_type import MotionPhaseType
from spells.spell_match import SpellMatch
from spells.spell_matcher_manager import SpellMatcherManager


class SpellTraceSessionManager:
    """
    Owns a 'current attempt' tracer. Starts on MOVING, always passes a valid tracer
    (real or NullSpellTrace) to matcher.try_match(), and flushes on match or natural break.
    """

    def __init__(
        self, logger: Logger, trace_factory: SpellTraceAdapterFactory, start_active: bool, settings: SpellTraceSessionSettings
    ) -> None:
        self._logger = logger
        self._trace_factory = trace_factory
        self._settings = settings
        self._enabled: bool = start_active

        # Always hold a tracer (Null until an attempt starts)
        self._trace: SpellTrace = NullSpellTrace()
        self._in_active_trace: bool = False  # whether we're inside an active attempt

    # --- control ---
    def set_enabled(self, enabled: bool) -> None:
        if not enabled and self._in_active_trace:
            self.flush("tracing-off")
        self._enabled = enabled
        if not enabled:
            # ensure we’re back to a clean Null tracer
            self._trace = NullSpellTrace()
            self._in_active_trace = False

    def toggle(self) -> None:
        self.set_enabled(not self._enabled)
        self._logger.info(f"Tracing {'ENABLED' if self._enabled else 'DISABLED'}")

    # --- hooks you call from your app ---
    def on_motion_changed(self, mode: MotionPhaseType) -> None:
        # Start a new attempt on real motion
        if self._enabled and mode == MotionPhaseType.MOVING and not self._in_active_trace:
            self._trace = self._trace_factory.create()
            self._in_active_trace = True
            self._logger.debug(f"[{self._settings.label_prefix}] trace START")

    def on_segment(
        self,
        segment: GestureSegment,
        history_tail: Sequence[GestureSegment],
        matcher_manager: SpellMatcherManager,
    ) -> None:
        """
        Feed the tracer into matching each time a segment completes.
        If the segment is a long NONE, flush (natural break).
        """
        matcher_manager.try_match(history_tail)

        # Natural break: end attempt after a long NONE
        if segment.direction_type == DirectionType.NONE and segment.duration_s >= self._settings.natural_break_s:
            self.flush("break")

    def on_match(
        self,
        match: SpellMatch,
    ) -> None:
        # Successful attempt ends the trace
        self.flush("match")

    def on_difficulty_changed(self) -> None:
        # Changing models? close any ongoing attempt
        self.flush("difficulty-changed")

    def flush(self, reason: str = "") -> None:
        if not self._in_active_trace:
            self._logger.debug(f"[{self._settings.label_prefix} {reason}] skip flush: no active trace")
            return
        # Prefer adapter.a.pretty(); otherwise fall back to tracer.pretty()
        attempt_obj = getattr(self._trace, "a", None)
        text = None
        if attempt_obj is not None and hasattr(attempt_obj, "pretty"):
            text = attempt_obj.pretty()
        elif hasattr(self._trace, "pretty"):
            text = self._trace.pretty()
        if text:
            self._logger.debug(f"[{self._settings.label_prefix} {reason}]\n{text}")
        else:
            self._logger.debug(f"[{self._settings.label_prefix} {reason}] finished attempt (no pretty payload)")
        # Reset to Null tracer
        self._trace = NullSpellTrace()
        self._in_active_trace = False
