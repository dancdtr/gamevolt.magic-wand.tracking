from logging import Logger
from typing import Sequence

from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.matching.rules.rules_validator import RulesValidator
from spells.matching.spell_match_context import SpellMatchContext
from spells.matching.spell_match_metrics import SpellMatchMetrics
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_matcher_base import SpellMatcherBase
from spells.spell_step import SpellStep


class SpellMatcher(SpellMatcherBase):
    def __init__(self, logger: Logger, accuracy_scorer: SpellAccuracyScorer, spells: list[SpellDefinition]) -> None:
        super().__init__(logger, spells)
        self._accuracy_scorer = accuracy_scorer
        self._rules_validator = RulesValidator()

    # ─── Public API ──────────────────────────────────────────────────────────

    def _match_spell(self, spell: SpellDefinition, compressed: Sequence[GestureSegment]) -> SpellMatch | None:
        if not compressed:
            return None

        flat_steps, group_idx_of_step = self._flatten_with_group_map(spell)

        # try windows starting at each index from newest back
        for start_idx in range(len(compressed) - 1, -1, -1):
            match = self._match_from_index(spell, flat_steps, group_idx_of_step, compressed, start_idx)
            if match:
                return match

        return None

    # ─── Internal helpers ────────────────────────────────────────────────────

    def _flatten_with_group_map(self, spell: SpellDefinition) -> tuple[list[SpellStep], list[int]]:
        flat: list[SpellStep] = []
        group_map: list[int] = []
        for gi, grp in enumerate(spell.step_groups):
            for st in grp.steps:
                flat.append(st)
                group_map.append(gi)
        return flat, group_map

    def _match_from_index(
        self,
        spell: SpellDefinition,
        flat_steps: Sequence[SpellStep],
        group_idx_of_step: Sequence[int],
        segs: Sequence[GestureSegment],
        i_start: int,
    ) -> SpellMatch | None:

        # reversed because we walk newest→oldest
        steps = list(reversed(flat_steps))
        step_to_group = list(reversed(group_idx_of_step))

        step_count = len(steps)
        required_total = sum(1 for st in steps if st.required)
        optional_total = step_count - required_total

        step_idx = 0
        start_ts: int | None = None
        end_ts: int | None = None
        total_duration = 0.0

        group_count = len(spell.step_groups)
        group_distance = [0.0 for _ in range(group_count)]
        group_duration = [0.0 for _ in range(group_count)]
        total_distance = 0.0

        filler_duration = 0.0

        matched_required = 0
        matched_optional = 0

        used_min_idx: int | None = None  # oldest in this window
        used_max_idx: int | None = None  # newest in this window

        group_names = [g.name for g in spell.step_groups]

        i = i_start
        while i >= 0 and step_idx < step_count:
            seg = segs[i]
            current_idx = i

            # capture time window endpoints (chronologically correct)
            if start_ts is None:
                start_ts = seg.start_ts_ms
            end_ts = seg.end_ts_ms

            dt = seg.duration_s
            dist = seg.path_length
            step = steps[step_idx]

            seg_dir_name = seg.direction_type.name
            step_dirs = {d.name for d in step.allowed}
            seg_idx_in_window = i_start - i  # 0 = newest

            def log_group_state(prefix: str) -> None:
                if total_distance > 0:
                    ratios = [gd / total_distance for gd in group_distance]
                else:
                    ratios = [0.0 for _ in group_distance]

                self._logger.debug(
                    "%s spell=%s win_start=%d seg_win_idx=%d dir=%s "
                    "step_idx=%d/%d required=%s dist=%.3f dt=%.3f "
                    "group_distance=%s group_ratios=%s",
                    prefix,
                    spell.name,
                    i_start,
                    seg_idx_in_window,
                    seg_dir_name,
                    step_idx,
                    step_count,
                    step.required,
                    dist,
                    dt,
                    dict(zip(group_names, group_distance)),
                    dict(zip(group_names, [round(r, 3) for r in ratios])),
                )

            def mark_used_index(idx: int) -> None:
                nonlocal used_min_idx, used_max_idx
                if used_min_idx is None or idx < used_min_idx:
                    used_min_idx = idx
                if used_max_idx is None or idx > used_max_idx:
                    used_max_idx = idx

            def try_consume_as_filler() -> bool:
                nonlocal filler_duration, total_duration, i

                # still keep the semantic that long NONE gaps break the window
                if seg.direction_type == DirectionType.NONE and dt > spell.max_idle_gap_s:
                    return False

                filler_duration += dt
                total_duration += dt

                gi_filler = step_to_group[step_idx]
                group_distance[gi_filler] += dist
                # group_duration[gi_filler] += dt  # optional

                mark_used_index(current_idx)
                log_group_state("FILLER")

                i -= 1
                return True

            # NONE segments are always potential filler
            if seg.direction_type == DirectionType.NONE:
                if not try_consume_as_filler():
                    self._logger.debug(
                        "NONE segment rejected as filler: spell=%s seg_win_idx=%d dt=%.3f",
                        spell.name,
                        seg_idx_in_window,
                        dt,
                    )
                    return None
                continue

            # check this segment against the current step
            dir_ok = seg.direction_type in step.allowed
            dur_ok = dt >= step.min_duration_s

            # ─── Match branch ───────────────────────────────────────
            if dir_ok and dur_ok:
                total_duration += dt
                total_distance += dist

                gi = step_to_group[step_idx]
                group_distance[gi] += dist
                group_duration[gi] += dt

                if step.required:
                    matched_required += 1
                else:
                    matched_optional += 1

                mark_used_index(current_idx)
                log_group_state("MATCH ")

                step_idx += 1
                i -= 1
                continue

            # ─── Mismatch branch ────────────────────────────────────

            self._logger.debug(
                "MISMATCH spell=%s win_start=%d seg_win_idx=%d dir=%s step_idx=%d/%d " "step_allowed=%s dt=%.3f dist=%.3f required=%s",
                spell.name,
                i_start,
                seg_idx_in_window,
                seg_dir_name,
                step_idx,
                step_count,
                step_dirs,
                dt,
                dist,
                step.required,
            )

            if not step.required:
                # OPTIONAL STEP:
                # Skip it and re-check same segment against next step.
                step_idx += 1
                continue

            # REQUIRED STEP:

            # Try to treat this segment as filler between required steps.
            if try_consume_as_filler():
                continue

            # Required step not satisfied and can't be filler → this window dies.
            self._logger.debug(
                "REQUIRED step failed and not filler: spell=%s seg_win_idx=%d step_idx=%d",
                spell.name,
                seg_idx_in_window,
                step_idx,
            )
            return None

        # ─── Build metrics & run rules ───────────────────────────────────────

        total_used = matched_required + matched_optional

        # If we didn't match any required steps or never set timestamps,
        # there's nothing meaningful to evaluate.
        if matched_required == 0 or start_ts is None or end_ts is None:
            return None

        # derive window indices
        if used_min_idx is None or used_max_idx is None:
            window_start_index = i_start
            window_end_index = i_start
        else:
            window_start_index = used_min_idx
            window_end_index = used_max_idx

        metrics = SpellMatchMetrics(
            total_duration_s=total_duration,
            filler_duration_s=filler_duration,
            total_distance=total_distance,
            group_distance=group_distance,
            group_duration_s=group_duration,
            used_steps=total_used,
            total_steps=len(flat_steps),
            required_matched=matched_required,
            required_total=required_total,
            optional_matched=matched_optional,
            optional_total=optional_total,
        )

        ctx = SpellMatchContext(
            spell=spell,
            segments=segs,
            metrics=metrics,
            window_start_index=window_start_index,
            window_end_index=window_end_index,
        )

        # ALL validation now lives in rules
        if not self._rules_validator.validate(ctx):
            self._logger.debug(
                "NO MATCH (rule validator): spell=%s win_start=%d " "matched_required=%d/%d total_used=%d",
                spell.name,
                i_start,
                matched_required,
                required_total,
                total_used,
            )
            return None

        # If we get here, the candidate passed all rules.
        accuracy = self._accuracy_scorer.calculate(spell, metrics)

        if total_distance > 0:
            final_ratios = [gd / total_distance for gd in group_distance]
        else:
            final_ratios = [0.0 for _ in group_distance]

        self._logger.info(
            "MATCHED spell=%s score=%.3f win_start=%d "
            "required %d/%d + optional %d/%d = total %d/%d "
            "total_distance=%.3f group_distance=%s group_ratios=%s filler_duration=%.3f",
            spell.name,
            accuracy.score,
            i_start,
            matched_required,
            required_total,
            matched_optional,
            optional_total,
            total_used,
            required_total + optional_total,
            total_distance,
            dict(zip(group_names, group_distance)),
            dict(zip(group_names, [round(r, 3) for r in final_ratios])),
            filler_duration,
        )

        return SpellMatch(
            spell_id=spell.id,
            spell_name=spell.name,
            start_ts_ms=start_ts,
            end_ts_ms=end_ts,
            duration_s=total_duration,
            segments_used=total_used,
            total_segments=len(flat_steps),
            required_matched=matched_required,
            required_total=required_total,
            optional_matched=matched_optional,
            optional_total=optional_total,
            filler_duration_s=filler_duration,
            accuracy_score=accuracy.score,
        )
