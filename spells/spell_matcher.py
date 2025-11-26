from __future__ import annotations

from logging import Logger
from typing import Sequence

from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.matching.rules.distance_rule import DurationRule
from spells.matching.rules.duration_rule import DistanceRule
from spells.matching.rules.group_distance_duration_rule import GroupDistanceRatioRule
from spells.matching.rules.spell_rule import SpellRule
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

    def _build_rules(self, spell: SpellDefinition) -> list[SpellRule]:
        rules: list[SpellRule] = []

        if spell.check_duration:
            rules.append(DurationRule())

        if spell.check_distance:
            rules.append(DistanceRule())

        if spell.check_group_distance_ratio:
            rules.append(GroupDistanceRatioRule())

        # TODO: add GroupDurationRatioRule and YAML-driven rules here

        return rules

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

        def would_exceed_total_duration(extra: float) -> bool:
            if spell.max_total_duration_s is None:
                return False
            return (total_duration + extra) > spell.max_total_duration_s

        rules = self._build_rules(spell)

        # helpful labels for logging
        group_names = [g.name for g in spell.step_groups]

        i = i_start
        while i >= 0 and step_idx < step_count:
            seg = segs[i]

            # capture time window endpoints (chronologically correct)
            if start_ts is None:
                start_ts = seg.start_ts_ms
            end_ts = seg.end_ts_ms

            dt = seg.duration_s
            dist = seg.path_length
            step = steps[step_idx]

            seg_dir_name = seg.direction_type.name
            step_dirs = {d.name for d in step.allowed}

            # for logging: segment index within this window (0 = newest)
            seg_idx_in_window = i_start - i

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

            def try_consume_as_filler() -> bool:
                nonlocal filler_duration, total_duration, i

                # optional hard per-seg limit for NONE gaps
                if seg.direction_type == DirectionType.NONE and dt > spell.max_idle_gap_s:
                    return False

                # respect overall filler budget
                if filler_duration + dt > spell.max_filler_duration_s:
                    return False

                # respect overall spell window
                if would_exceed_total_duration(dt):
                    return False

                filler_duration += dt
                total_duration += dt

                # attribute this filler distance to the group of the
                # step we're currently trying to match.
                gi_filler = step_to_group[step_idx]
                group_distance[gi_filler] += dist
                # group_duration[gi_filler] += dt  # if you want duration, too

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
                if would_exceed_total_duration(dt):
                    self._logger.debug(
                        "MATCH would exceed max_total_duration: spell=%s seg_win_idx=%d dt=%.3f",
                        spell.name,
                        seg_idx_in_window,
                        dt,
                    )
                    return None

                total_duration += dt
                total_distance += dist

                gi = step_to_group[step_idx]
                group_distance[gi] += dist
                group_duration[gi] += dt

                if step.required:
                    matched_required += 1
                else:
                    matched_optional += 1

                log_group_state("MATCH ")

                step_idx += 1
                i -= 1
                continue

            # ─── Mismatch branch ────────────────────────────────────

            # At this point: seg does NOT satisfy the current step
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
                # Don't burn filler here. Just skip this step and
                # re-check the same segment against the next step.
                step_idx += 1
                continue

            # REQUIRED STEP:

            # First, see if we can treat this segment as filler between
            # required steps without advancing step_idx.
            if try_consume_as_filler():
                continue

            # Required step not satisfied and can't be filler -> fail this window
            self._logger.debug(
                "REQUIRED step failed and not filler: spell=%s seg_win_idx=%d step_idx=%d",
                spell.name,
                seg_idx_in_window,
                step_idx,
            )
            return None

        # ─── End condition & rule checks ───────────────────────────

        # Any required steps left unvisited?
        remaining_required = any(st.required for st in steps[step_idx:])

        if remaining_required:
            self._logger.debug(
                "NO MATCH (remaining required steps): spell=%s win_start=%d " "matched_required=%d/%d step_idx=%d/%d",
                spell.name,
                i_start,
                matched_required,
                required_total,
                step_idx,
                step_count,
            )
            return None

        total_used = matched_required + matched_optional

        if matched_required == required_total and total_used >= spell.min_spell_steps and start_ts is not None and end_ts is not None:
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
            )

            for rule in rules:
                if not rule.validate(ctx):
                    self._logger.debug(
                        "NO MATCH (rule failed): spell=%s rule=%s total_distance=%.3f group_distance=%s",
                        spell.name,
                        rule,
                        total_distance,
                        dict(zip(group_names, group_distance)),
                    )
                    return None

            accuracy = self._accuracy_scorer.calculate(spell, metrics)

            # final ratios for this match
            if total_distance > 0:
                final_ratios = [gd / total_distance for gd in group_distance]
            else:
                final_ratios = [0.0 for _ in group_distance]

            print(f"score: {100*accuracy.score:.3f}%")

            self._logger.info(
                "MATCHED spell=%s score=%d win_start=%d  "
                "required %d/%d + optional %d/%d = total %d/%d "
                "total_distance=%.3f group_distance=%s: group_ratios=%s filler_duration=%.3f",
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

            # self._logger.info(
            #     "Matched %s: required=%d/%d optional=%d/%d total_used=%d " "total_distance=%.3f filler=%.3f",
            #     spell.name,
            #     matched_required,
            #     required_total,
            #     matched_optional,
            #     optional_total,
            #     total_used,
            #     total_distance,
            #     filler_duration,
            # )

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

        # Debug fallback if you want:
        self._logger.debug(
            "NO MATCH (final check): spell=%s win_start=%d " "matched_required=%d/%d total_used=%d/%d " "start_ts_set=%s end_ts_set=%s",
            spell.name,
            i_start,
            matched_required,
            required_total,
            total_used,
            spell.min_spell_steps,
            start_ts is not None,
            end_ts is not None,
        )

        return None
