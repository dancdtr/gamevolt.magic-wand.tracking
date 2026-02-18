# spells/matching/engine/spell_window_matcher.py
from __future__ import annotations

from logging import Logger
from typing import Sequence

from motion.gesture.gesture_segment import GestureSegment
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.matching.compile.spell_compiler import CompiledSpell
from spells.matching.engine.match_state import MatchState
from spells.matching.engine.spell_window_matcher_debugger import SpellWindowMatcherDebugger
from spells.matching.policies.filler_policy import FillerPolicy
from spells.matching.rules.rules_validator import RulesValidator
from spells.matching.spell_match_context import SpellMatchContext
from spells.matching.spell_match_metrics import SpellMatchMetrics
from spells.spell_match import SpellMatch
from spells.spell_step import SpellStep


class SpellWindowMatcher:
    def __init__(
        self,
        logger: Logger,
        accuracy_scorer: SpellAccuracyScorer,
        rules_validator: RulesValidator,
        filler_policy: FillerPolicy,
    ) -> None:
        self._accuracy_scorer = accuracy_scorer
        self._rules_validator = rules_validator
        self._filler = filler_policy
        self._debugger = SpellWindowMatcherDebugger(logger)

    def match(
        self,
        wand_id: str,
        spell_id: str,
        spell_name: str,
        compiled: CompiledSpell,
        segments: Sequence[GestureSegment],
    ) -> SpellMatch | None:
        if not segments:
            return None

        seen_windows: set[tuple[int, int]] = set()

        for i_start in range(len(segments) - 1, -1, -1):
            match = self._attempt_window(
                wand_id=wand_id,
                spell_id=spell_id,
                spell_name=spell_name,
                compiled=compiled,
                segs=segments,
                i_start=i_start,
                seen_windows=seen_windows,
            )
            if match is not None:
                return match

        return None

    def _attempt_window(
        self,
        *,
        wand_id: str,
        spell_id: str,
        spell_name: str,
        compiled: CompiledSpell,
        segs: Sequence[GestureSegment],
        i_start: int,
        seen_windows: set[tuple[int, int]],
    ) -> SpellMatch | None:
        steps = compiled.steps_rev
        step_to_group = compiled.step_to_group_rev
        step_count = len(steps)

        state = MatchState(
            step_idx=0,
            group_distance=[0.0 for _ in range(compiled.group_count)],
            group_duration_s=[0.0 for _ in range(compiled.group_count)],
            group_steps_matched=[0 for _ in range(compiled.group_count)],
        )

        i = i_start
        while i >= 0 and state.step_idx < step_count:
            seg = segs[i]
            step = steps[state.step_idx]
            seg_idx_in_window = i_start - i

            if self._seg_matches_step(seg, step):
                self._consume_match(
                    state=state,
                    seg=seg,
                    step=step,
                    group_idx=step_to_group[state.step_idx],
                    current_idx=i,
                )
                self._debugger.on_step_consumed(
                    spell_name=spell_name,
                    i_start=i_start,
                    seg_idx_in_window=seg_idx_in_window,
                    seg=seg,
                    step=step,
                    compiled=compiled,
                    state=state,
                )
                state.step_idx += 1
                i -= 1
                continue

            self._debugger.on_mismatch(spell_name, i_start, seg_idx_in_window, seg, step, state, step_count)

            if not step.required:
                state.step_idx += 1
                continue

            if self._consume_filler(
                state=state,
                compiled=compiled,
                seg=seg,
                current_step=step,
                current_group_idx=step_to_group[state.step_idx],
                current_idx=i,
                seg_idx_in_window=seg_idx_in_window,
                spell_name=spell_name,
                i_start=i_start,
            ):
                i -= 1
                continue

            self._debugger.on_required_step_failed(spell_name, seg_idx_in_window, state.step_idx)
            return None

        if state.matched_required == 0:
            return None

        window_start_index, window_end_index = self._window_indices(state, i_start)
        window_key = (window_start_index, window_end_index)

        if window_key in seen_windows:
            self._debugger.on_skip_duplicate(spell_name, i_start, window_key)
            return None
        seen_windows.add(window_key)

        metrics = self._build_metrics(compiled, state)

        ctx = SpellMatchContext(
            spell=compiled.definition,
            segments=segs,
            metrics=metrics,
            window_start_index=window_start_index,
            window_end_index=window_end_index,
        )

        if not self._rules_validator.validate(ctx):
            self._debugger.on_rules_failed(spell_name, i_start, window_key, compiled, state)
            return None

        accuracy = self._accuracy_scorer.calculate(compiled.definition, metrics)
        self._debugger.on_match(spell_name, i_start, window_key, compiled, state, accuracy.score)

        start_ts = segs[window_start_index].start_ts_ms
        end_ts = segs[window_end_index].end_ts_ms
        used_steps_scorable = state.matched_required + state.matched_optional

        return SpellMatch(
            wand_id=wand_id,
            spell_id=spell_id,
            spell_name=spell_name,
            start_ts_ms=start_ts,
            end_ts_ms=end_ts,
            duration_s=state.total_duration_s,
            segments_used=used_steps_scorable,
            total_segments=compiled.scorable_total,
            required_matched=state.matched_required,
            required_total=compiled.required_total,
            optional_matched=state.matched_optional,
            optional_total=compiled.optional_total,
            filler_duration_s=state.filler_duration_s,
            accuracy_score=accuracy.score,
        )

    # ------------------------------------------------------------------ #
    # Core predicates + consumers
    # ------------------------------------------------------------------ #

    def _seg_matches_step(self, seg: GestureSegment, step: SpellStep) -> bool:
        if seg.direction_type not in step.allowed:
            return False
        dt = seg.duration_s
        max_dur = getattr(step, "max_duration_s", None)
        return dt >= step.min_duration_s and (max_dur is None or dt <= max_dur)

    def _consume_match(
        self,
        *,
        state: MatchState,
        seg: GestureSegment,
        step: SpellStep,
        group_idx: int,
        current_idx: int,
    ) -> None:
        state.total_duration_s += seg.duration_s
        self._mark_used_index(state, current_idx)

        if step.is_pause:
            state.matched_pause += 1
            state.pause_duration_s += seg.duration_s
            return

        state.total_distance += seg.path_length
        state.group_distance[group_idx] += seg.path_length
        state.group_duration_s[group_idx] += seg.duration_s
        state.group_steps_matched[group_idx] += 1

        if step.required:
            state.matched_required += 1
        else:
            state.matched_optional += 1

    def _consume_filler(
        self,
        *,
        state: MatchState,
        compiled: CompiledSpell,
        seg: GestureSegment,
        current_step: SpellStep,
        current_group_idx: int,
        current_idx: int,
        seg_idx_in_window: int,
        spell_name: str,
        i_start: int,
    ) -> bool:
        res = self._filler.try_consume(
            compiled=compiled,
            seg=seg,
            current_step=current_step,
            current_group_idx=current_group_idx,
            last_scorable_allowed=None,
            last_scorable_group_idx=None,
        )
        if not res.consumed:
            return False

        state.total_duration_s += res.duration_s
        self._mark_used_index(state, current_idx)

        state.filler_duration_s += res.duration_s
        if not res.is_absorbed and not self._filler.is_idle_dir(seg.direction_type):
            state.group_distance[current_group_idx] += seg.path_length

        self._debugger.on_filler_consumed(
            spell_name=spell_name,
            i_start=i_start,
            seg_idx_in_window=seg_idx_in_window,
            seg=seg,
            step=current_step,
            compiled=compiled,
            state=state,
        )

        return True

    # ------------------------------------------------------------------ #
    # Window/metrics helpers
    # ------------------------------------------------------------------ #

    def _window_indices(self, state: MatchState, i_start: int) -> tuple[int, int]:
        if state.used_min_idx is None or state.used_max_idx is None:
            return i_start, i_start
        return state.used_min_idx, state.used_max_idx

    def _build_metrics(self, compiled: CompiledSpell, state: MatchState) -> SpellMatchMetrics:
        used_steps_scorable = state.matched_required + state.matched_optional
        return SpellMatchMetrics(
            total_duration_s=state.total_duration_s,
            filler_duration_s=state.filler_duration_s,
            total_distance=state.total_distance,
            group_distance=state.group_distance,
            group_duration_s=state.group_duration_s,
            group_steps_matched=state.group_steps_matched,
            used_steps=used_steps_scorable,
            total_steps=compiled.scorable_total,
            required_matched=state.matched_required,
            required_total=compiled.required_total,
            optional_matched=state.matched_optional,
            optional_total=compiled.optional_total,
        )

    def _mark_used_index(self, state: MatchState, idx: int) -> None:
        if state.used_min_idx is None or idx < state.used_min_idx:
            state.used_min_idx = idx
        if state.used_max_idx is None or idx > state.used_max_idx:
            state.used_max_idx = idx
