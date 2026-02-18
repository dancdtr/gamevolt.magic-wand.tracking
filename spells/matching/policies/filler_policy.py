# spells/matching/policies/filler_policy.py
from __future__ import annotations

from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from spells.matching.compile.spell_compiler import CompiledSpell
from spells.matching.policies.filler_result import FillerResult
from spells.spell_step import SpellStep


class FillerPolicy:
    """
    Encapsulates:
      - which segments can be consumed as filler
      - idle-gap breaking behaviour
      - optional "absorbable jitter" behaviour

    The window matcher owns the state (used_min/max idx etc.).
    This policy only decides HOW a segment should be treated.

    - idle direction segments count as filler and can break if too long
    - non-idle mismatches count as filler (do not break) and (optionally) add distance bookkeeping elsewhere

    If you enable absorption in SpellDefinition (via attributes):
      - absorb_max_duration_s (default 0.15)
      - absorb_adjacent_tol (default 1)
    then short, direction-adjacent segments can be "absorbed" instead of filler.
    """

    def __init__(self) -> None:

        # 8-way direction indexing for adjacency (clockwise from E)
        self._dir_index: dict[DirectionType, int] = {
            DirectionType.MOVING_E: 0,
            DirectionType.MOVING_NE: 1,
            DirectionType.MOVING_N: 2,
            DirectionType.MOVING_NW: 3,
            DirectionType.MOVING_W: 4,
            DirectionType.MOVING_SW: 5,
            DirectionType.MOVING_S: 6,
            DirectionType.MOVING_SE: 7,
        }

    def is_idle_dir(self, d: DirectionType) -> bool:
        return d in (DirectionType.PAUSE, DirectionType.UNKNOWN)

    def try_consume(
        self,
        *,
        compiled: CompiledSpell,
        seg: GestureSegment,
        current_step: SpellStep,
        current_group_idx: int,
        last_scorable_allowed: frozenset[DirectionType] | None,
        last_scorable_group_idx: int | None,
    ) -> FillerResult:
        """
        Decide if `seg` can be consumed as filler, and if so whether it should be absorbed.

        Returns:
          - consumed=False => caller should treat as "can't be filler" (usually fail required step)
          - consumed=True, is_absorbed=False => true filler
          - consumed=True, is_absorbed=True  => absorbed jitter (credit to group_idx)
        """
        dt = seg.duration_s
        dist = seg.path_length
        spell = compiled.definition

        # Hard break: long idle gap
        if self.is_idle_dir(seg.direction_type) and dt > spell.max_idle_gap_s:
            return FillerResult(consumed=False, is_absorbed=False, duration_s=dt, distance=dist)

        # Idle directions are never absorbed
        if self.is_idle_dir(seg.direction_type):
            return FillerResult(consumed=True, is_absorbed=False, duration_s=dt, distance=dist)

        # Optional absorbable jitter
        absorb_max_s = float(getattr(spell, "absorb_max_duration_s", 0.15))
        absorb_adjacent_tol = int(getattr(spell, "absorb_adjacent_tol", 1))

        if dt <= absorb_max_s:
            best_gi: int | None = None
            best_adj: int | None = None

            # Candidate A: absorb towards the current step (only if scorable)
            if current_step.is_scorable:
                adj = self._min_adj_to_allowed(seg.direction_type, current_step.allowed)
                if adj is not None and adj <= absorb_adjacent_tol:
                    best_adj = adj
                    best_gi = current_group_idx

            # Candidate B: absorb towards the last matched scorable step
            if last_scorable_allowed is not None and last_scorable_group_idx is not None:
                adj = self._min_adj_to_allowed(seg.direction_type, last_scorable_allowed)
                if adj is not None and adj <= absorb_adjacent_tol:
                    if best_adj is None or adj < best_adj:
                        best_adj = adj
                        best_gi = last_scorable_group_idx

            if best_gi is not None:
                return FillerResult(
                    consumed=True,
                    is_absorbed=True,
                    duration_s=dt,
                    distance=dist,
                    group_idx=best_gi,
                    adj=best_adj,
                )

        # Otherwise: true filler
        return FillerResult(consumed=True, is_absorbed=False, duration_s=dt, distance=dist)

    # ----- adjacency helpers -----
    def _adj_dist(self, a: DirectionType, b: DirectionType) -> int | None:
        ia = self._dir_index.get(a)
        ib = self._dir_index.get(b)
        if ia is None or ib is None:
            return None
        d = abs(ia - ib)
        return min(d, 8 - d)

    def _min_adj_to_allowed(self, seg_dir: DirectionType, allowed: frozenset[DirectionType]) -> int | None:
        best: int | None = None
        for d in allowed:
            dist = self._adj_dist(seg_dir, d)
            if dist is None:
                continue
            if best is None or dist < best:
                best = dist
        return best
