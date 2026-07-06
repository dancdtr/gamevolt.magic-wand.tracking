"""Assembles closed stroke segments into cast attempts, deciding when to commit.

The phase tracker can't distinguish "long corner pause" from "end of spell" at the moment
stillness begins, so segment boundaries are treated as *provisional* and recognition
itself arbitrates:

- A segment closing at HOLDING is buffered and evaluated (alone and joined with recent
  segments). A gate-passing match commits immediately; a weak one is held — if motion
  resumes, the next segment joins it, so an over-long corner pause no longer splits a
  glyph.
- A transient PAUSED exposes the still-open stroke. A match clearing the stricter
  `soft_commit_accuracy` bar commits without waiting for a settle, covering players who
  never sufficiently stop after casting.
- STOPPED (a true settle, which also resets the path origin) resolves the buffer: the
  best failed evaluation surfaces as a single miscast — unless a commit just happened,
  in which case trailing motion is dropped silently.

Gates are never loosened: every commit passes the same scoring gates as before, only the
segmentation around them is forgiving.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging import Logger
from motion.stroke.stroke_windower import Stroke, join_strokes
from spells.matching.dollar_one.dollar_one_recognizer import Recognition
from spells.scoring.cast_score import CastScore
from wand.configuration.cast_assembly_settings import CastAssemblySettings


@dataclass(frozen=True)
class CastEvaluation:
    """One candidate stroke taken through recognition + scoring."""

    stroke: Stroke
    results: list[Recognition]  # best first
    cast: CastScore


class CastAssembler:
    def __init__(
        self,
        logger: Logger,
        settings: CastAssemblySettings,
        evaluate: Callable[[Stroke], CastEvaluation | None],
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._logger = logger
        self._settings = settings
        self._evaluate = evaluate
        self._now = now

        self.committed: Event[Callable[[CastEvaluation], None]] = Event()
        self.rejected: Event[Callable[[CastEvaluation], None]] = Event()

        self._segments: list[Stroke] = []
        self._pending: CastEvaluation | None = None
        self._last_commit_at: float | None = None

    def reset(self) -> None:
        self._segments.clear()
        self._pending = None

    def on_segment(self, segment: Stroke) -> None:
        """A stroke closed at HOLDING: buffer it and commit if any suffix join passes."""
        self._prune(segment.end_ts_ms)
        self._segments.append(segment)
        del self._segments[: -self._settings.max_join_segments]

        best = self._best_candidate(self._segments)
        if best is None:
            return
        if best.cast.recognized:
            self._commit(best)
        else:
            # Hold as the would-be miscast; a resuming stroke may still complete the glyph.
            self._pending = best

    def on_provisional(self, provisional: Stroke) -> bool:
        """A transient PAUSED exposed the open stroke. Commits (returning True, so the
        caller aborts the open stroke) only past the stricter soft-commit accuracy bar."""
        self._prune(provisional.end_ts_ms)
        best = self._best_candidate([*self._segments, provisional])
        if best is None:
            return False
        if best.cast.recognized and best.cast.match_accuracy >= self._settings.soft_commit_accuracy:
            self._logger.debug(
                f"Cast assembler soft-commit at PAUSED: '{best.cast.label}' "
                f"({best.cast.match_accuracy * 100:.1f}%)."
            )
            self._commit(best)
            return True
        return False

    def on_stopped(self) -> None:
        """A true settle: resolve the buffer. Anything unrecognised surfaces as one miscast."""
        pending = self._pending
        self._pending = None
        self._segments.clear()
        if pending is None:
            return

        suppression = self._settings.post_commit_suppression_s
        if self._last_commit_at is not None and self._now() - self._last_commit_at < suppression:
            self._logger.debug(f"Cast assembler dropped post-commit trailing motion ('{pending.cast.label}').")
            return
        self.rejected.invoke(pending)

    def _commit(self, evaluation: CastEvaluation) -> None:
        self._segments.clear()
        self._pending = None
        self._last_commit_at = self._now()
        self.committed.invoke(evaluation)

    def _best_candidate(self, segments: list[Stroke]) -> CastEvaluation | None:
        """Best evaluation over suffix joins: newest segment alone, then joined with each
        older neighbour in turn. Suffixes (not subsets) because junk precedes a glyph far
        more often than it interleaves one."""
        best: CastEvaluation | None = None
        for join_count in range(1, min(len(segments), self._settings.max_join_segments) + 1):
            candidate = segments[-1] if join_count == 1 else join_strokes(segments[-join_count:])
            evaluation = self._evaluate(candidate)
            if evaluation is None:
                continue
            if best is None or self._better(evaluation, best):
                best = evaluation
        return best

    @staticmethod
    def _better(a: CastEvaluation, b: CastEvaluation) -> bool:
        if a.cast.recognized != b.cast.recognized:
            return a.cast.recognized
        return a.cast.match_accuracy > b.cast.match_accuracy

    def _prune(self, newest_ts_ms: int) -> None:
        max_age_ms = self._settings.max_segment_age_s * 1000.0
        self._segments = [s for s in self._segments if newest_ts_ms - s.end_ts_ms <= max_age_ms]
