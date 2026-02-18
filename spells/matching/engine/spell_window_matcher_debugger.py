# spells/matching/engine/window_matcher_debugger.py
from __future__ import annotations

import logging
from logging import Logger

from motion.gesture.gesture_segment import GestureSegment
from spells.matching.compile.spell_compiler import CompiledSpell
from spells.matching.engine.match_state import MatchState
from spells.spell_step import SpellStep


class SpellWindowMatcherDebugger:
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    @property
    def enabled(self) -> bool:
        return self._logger.isEnabledFor(logging.DEBUG)

    # ──────────────────────────────────────────────────────────────────────
    # High-level events
    # ──────────────────────────────────────────────────────────────────────

    def on_skip_duplicate(self, spell_name: str, i_start: int, window_key: tuple[int, int]) -> None:
        if not self.enabled:
            return
        self._logger.debug(f"Skipping duplicate window={window_key} spell={spell_name} win_start={i_start}")

    def on_rules_failed(
        self, spell_name: str, i_start: int, window_key: tuple[int, int], compiled: CompiledSpell, state: MatchState
    ) -> None:
        if not self.enabled:
            return

        used_steps_scorable = state.matched_required + state.matched_optional
        self._logger.debug(
            f"NO MATCH (rules): spell={spell_name} win_start={i_start} window={window_key} "
            f"required={state.matched_required}/{compiled.required_total} used_scorable={used_steps_scorable}/{compiled.scorable_total} "
            f"pause_steps={state.matched_pause} pause_s={state.pause_duration_s:.3f}"
        )

    def on_required_step_failed(self, spell_name: str, seg_idx_in_window: int, step_idx: int) -> None:
        if not self.enabled:
            return
        self._logger.debug(f"REQUIRED step failed and not filler: spell={spell_name} seg_win_idx={seg_idx_in_window} step_idx={step_idx}")

    def on_mismatch(
        self,
        spell_name: str,
        i_start: int,
        seg_idx_in_window: int,
        seg: GestureSegment,
        step: SpellStep,
        state: MatchState,
        step_count: int,
    ) -> None:
        if not self.enabled:
            return

        step_dirs = {d.name for d in step.allowed}
        self._logger.debug(
            f"MISMATCH spell={spell_name} win_start={i_start} seg_win_idx={seg_idx_in_window} "
            f"dir={seg.direction_type.name} step_idx={state.step_idx}/{step_count} step_allowed={step_dirs} "
            f"dt={seg.duration_s:.3f} dist={seg.path_length:.3f} step_required={step.required} "
            f"step_is_pause={step.is_pause}"
        )

    # ──────────────────────────────────────────────────────────────────────
    # Per-segment state logging
    # ──────────────────────────────────────────────────────────────────────

    def on_step_consumed(
        self,
        *,
        spell_name: str,
        i_start: int,
        seg_idx_in_window: int,
        seg: GestureSegment,
        step: SpellStep,
        compiled: CompiledSpell,
        state: MatchState,
    ) -> None:
        self._log_group_state(
            prefix="MATCH(PAUSE)" if step.is_pause else "MATCH",
            spell_name=spell_name,
            i_start=i_start,
            seg_idx_in_window=seg_idx_in_window,
            seg=seg,
            step=step,
            compiled=compiled,
            state=state,
        )

    def on_filler_consumed(
        self,
        *,
        spell_name: str,
        i_start: int,
        seg_idx_in_window: int,
        seg: GestureSegment,
        step: SpellStep,
        compiled: CompiledSpell,
        state: MatchState,
    ) -> None:
        self._log_group_state(
            prefix="FILLER",
            spell_name=spell_name,
            i_start=i_start,
            seg_idx_in_window=seg_idx_in_window,
            seg=seg,
            step=step,
            compiled=compiled,
            state=state,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Final match logging
    # ──────────────────────────────────────────────────────────────────────

    def on_match(
        self,
        spell_name: str,
        i_start: int,
        window_key: tuple[int, int],
        compiled: CompiledSpell,
        state: MatchState,
        score: float,
    ) -> None:
        if not self.enabled:
            return

        used_steps_scorable = state.matched_required + state.matched_optional
        ratios = self._ratios(state.group_distance, state.total_distance)

        self._logger.debug(
            f"MATCHED spell={spell_name} score={score:.3f} win_start={i_start} window={window_key} "
            f"required={state.matched_required}/{compiled.required_total} optional={state.matched_optional}/{compiled.optional_total} "
            f"used_scorable={used_steps_scorable}/{compiled.scorable_total} pause_steps={state.matched_pause} pause_s={state.pause_duration_s:.3f} "
            f"total_duration={state.total_duration_s:.3f} total_distance={state.total_distance:.3f} "
            f"group_distance={dict(zip(compiled.group_names, state.group_distance))} "
            f"group_ratios={dict(zip(compiled.group_names, [round(r, 3) for r in ratios]))} "
            f"filler_duration={state.filler_duration_s:.3f}"
        )

    # ──────────────────────────────────────────────────────────────────────
    # Internals
    # ──────────────────────────────────────────────────────────────────────

    def _log_group_state(
        self,
        *,
        prefix: str,
        spell_name: str,
        i_start: int,
        seg_idx_in_window: int,
        seg: GestureSegment,
        step: SpellStep,
        compiled: CompiledSpell,
        state: MatchState,
    ) -> None:
        if not self.enabled:
            return

        ratios = self._ratios(state.group_distance, state.total_distance)
        self._logger.debug(
            f"{prefix} spell={spell_name} win_start={i_start} seg_win_idx={seg_idx_in_window} "
            f"dir={seg.direction_type.name} step_idx={state.step_idx}/{len(compiled.steps_rev)} step_required={step.required} "
            f"step_is_pause={step.is_pause} dist={seg.path_length:.3f} dt={seg.duration_s:.3f} "
            f"group_distance={dict(zip(compiled.group_names, state.group_distance))} "
            f"group_ratios={dict(zip(compiled.group_names, [round(r, 3) for r in ratios]))}"
        )

    @staticmethod
    def _ratios(values: list[float], total: float) -> list[float]:
        if total <= 0:
            return [0.0 for _ in values]
        return [v / total for v in values]
