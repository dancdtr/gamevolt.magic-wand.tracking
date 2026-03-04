# spells/spell_matcher.py
from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from logging import Logger

from gamevolt.events.event import Event
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.library.spell_definition_factory import SpellDefinitionFactory
from spells.matching.rules.rules_validator import RulesValidator
from spells.matching.spell_match_context import SpellMatchContext
from spells.matching.spell_match_metrics import SpellMatchMetrics
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_step import SpellStep
from spells.spell_type import SpellType


class SpellMatcher:
    def __init__(
        self,
        logger: Logger,
        accuracy_scorer: SpellAccuracyScorer,
    ) -> None:
        self._logger = logger

        self.matched: Event[Callable[[SpellMatch], None]] = Event()

        self._accuracy_scorer = accuracy_scorer
        self._rules_validator = RulesValidator()

        self._spell_definition_factory = SpellDefinitionFactory()

        self._target_spell_definition: SpellDefinition = self._spell_definition_factory.create_spell(SpellType.NONE)

    def set_spell_target(self, type: SpellType) -> None:
        self._target_spell_definition = self._spell_definition_factory.create_spell(type)

    # ----- public entry point -----
    def try_match(self, wand_id: str, history: Sequence[GestureSegment]) -> bool:
        if not history:
            return False

        compressed = self._compress(history)  # oldest → newest

        if self._target_spell_definition:
            match = self._match_spell(wand_id, self._target_spell_definition, compressed)
            if match:
                self._logger.info(f"({wand_id}) cast {match.spell_name}! ✨✨{match.accuracy_score * 100:.1f}% ({match.duration_s:.3f})")
                self.matched.invoke(match)
                return True

        return False

    # ----- helpers -----
    def _is_pause_step(self, step: SpellStep) -> bool:
        # Pause steps should match, but never count toward min_spell_steps / used_steps.
        return step.allowed == frozenset({DirectionType.PAUSE})

    def _compress(self, segments: Sequence[GestureSegment]) -> list[GestureSegment]:
        """
        Merge consecutive identical directions (including PAUSE/UNKNOWN),
        summing duration & path_length; recompute mean_speed accordingly.
        """
        if not segments:
            return []

        out: list[GestureSegment] = []
        cur = segments[0]
        for seg in segments[1:]:
            if seg.direction_type == cur.direction_type:
                total_dur = cur.duration_s + seg.duration_s
                total_path = cur.path_length + seg.path_length
                cur = type(cur)(
                    start_ts_ms=cur.start_ts_ms,
                    end_ts_ms=seg.end_ts_ms,
                    duration_s=total_dur,
                    sample_count=cur.sample_count + seg.sample_count,
                    direction_type=cur.direction_type,
                    avg_vec_x=0.0,
                    avg_vec_y=0.0,
                    net_dx=cur.net_dx + seg.net_dx,
                    net_dy=cur.net_dy + seg.net_dy,
                    mean_speed=(total_path / total_dur) if total_dur > 0 else 0.0,
                    path_length=total_path,
                )
            else:
                out.append(cur)
                cur = seg
        out.append(cur)
        return out

    # ----- matching implementation -----
    def _match_spell(
        self,
        wand_id: str,
        spell: SpellDefinition,
        compressed: Sequence[GestureSegment],
    ) -> SpellMatch | None:
        if not compressed:
            return None

        flat_steps, group_idx_of_step = self._flatten_with_group_map(spell)

        for start_idx in range(len(compressed) - 1, -1, -1):
            match = self._match_from_index(
                wand_id=wand_id,
                spell_definition=spell,
                flat_steps=flat_steps,
                group_idx_of_step=group_idx_of_step,
                segs=compressed,
                i_start=start_idx,
            )
            if match:
                return match

        return None

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
        wand_id: str,
        spell_definition: SpellDefinition,
        flat_steps: Sequence[SpellStep],
        group_idx_of_step: Sequence[int],
        segs: Sequence[GestureSegment],
        i_start: int,
    ) -> SpellMatch | None:
        """
        Walk newest→oldest and try to match reversed step list.

        Enhancements:
          - PAUSE steps can match, but never count toward min_spell_steps/used_steps.
          - "Absorbable jitter": short non-idle filler segments direction-adjacent to a neighbouring scorable step
            are credited into absorbed duration/distance and per-group absorbed metrics. They do NOT count as filler.
        """

        def is_idle_dir(d: DirectionType) -> bool:
            return d in (DirectionType.PAUSE, DirectionType.UNKNOWN)

        # 8-way direction indexing for adjacency (clockwise from E)
        dir_index: dict[DirectionType, int] = {
            DirectionType.MOVING_E: 0,
            DirectionType.MOVING_NE: 1,
            DirectionType.MOVING_N: 2,
            DirectionType.MOVING_NW: 3,
            DirectionType.MOVING_W: 4,
            DirectionType.MOVING_SW: 5,
            DirectionType.MOVING_S: 6,
            DirectionType.MOVING_SE: 7,
        }

        def _adj_dist(a: DirectionType, b: DirectionType) -> int | None:
            ia = dir_index.get(a)
            ib = dir_index.get(b)
            if ia is None or ib is None:
                return None
            d = abs(ia - ib)
            return min(d, 8 - d)

        def _min_adj_to_allowed(seg_dir: DirectionType, allowed: frozenset[DirectionType]) -> int | None:
            best: int | None = None
            for d in allowed:
                dist = _adj_dist(seg_dir, d)
                if dist is None:
                    continue
                if best is None or dist < best:
                    best = dist
            return best

        # Tunables (safe defaults; can move into SpellDefinition later)
        absorb_max_s = float(getattr(spell_definition, "absorb_max_duration_s", 0.15))
        absorb_adjacent_tol = int(getattr(spell_definition, "absorb_adjacent_tol", 1))

        # reversed because we walk newest→oldest
        steps = list(reversed(flat_steps))
        step_to_group = list(reversed(group_idx_of_step))

        step_count = len(steps)

        # Totals excluding PAUSE steps (so min_spell_steps can't be satisfied by pauses)
        scorable_total = sum(1 for st in steps if not self._is_pause_step(st))
        required_total = sum(1 for st in steps if st.required and not self._is_pause_step(st))
        optional_total = scorable_total - required_total

        matched_required = 0
        matched_optional = 0

        matched_pause = 0
        pause_duration_s = 0.0

        scorable_duration_s = 0.0

        absorbed_duration_s = 0.0
        absorbed_distance = 0.0

        filler_duration_s = 0.0  # TRUE filler only (absorbed jitter does not count)

        step_idx = 0

        total_duration_s = 0.0
        total_distance = 0.0  # scorable + absorbed only

        group_count = len(spell_definition.step_groups)
        group_distance = [0.0 for _ in range(group_count)]  # scorable only
        group_duration = [0.0 for _ in range(group_count)]  # scorable only
        group_steps_matched = [0 for _ in range(group_count)]  # scorable steps only

        group_absorbed_distance = [0.0 for _ in range(group_count)]
        group_absorbed_duration = [0.0 for _ in range(group_count)]

        used_min_idx: int | None = None  # oldest used segment in window
        used_max_idx: int | None = None  # newest used segment in window

        group_names = [g.name for g in spell_definition.step_groups]

        # Track last matched SCORABLE step so we can absorb jitter towards it
        last_scorable_allowed: frozenset[DirectionType] | None = None
        last_scorable_group_idx: int | None = None

        def mark_used_index(idx: int) -> None:
            nonlocal used_min_idx, used_max_idx
            if used_min_idx is None or idx < used_min_idx:
                used_min_idx = idx
            if used_max_idx is None or idx > used_max_idx:
                used_max_idx = idx

        def log_group_state(prefix: str, seg_idx_in_window: int, seg: GestureSegment, step: SpellStep) -> None:
            if not self._logger.isEnabledFor(logging.DEBUG):
                return

            total_effective_dist = total_distance
            ratios = [gd / total_effective_dist for gd in group_distance] if total_effective_dist > 0 else [0.0 for _ in group_distance]

            self._logger.debug(
                f"{prefix} spell={self._target_spell_definition.name} win_start={i_start} seg_win_idx={seg_idx_in_window} "
                f"dir={seg.direction_type.name} step_idx={step_idx}/{step_count} step_required={step.required} "
                f"step_is_pause={self._is_pause_step(step)} dist={seg.path_length:.3f} dt={seg.duration_s:.3f} "
                f"total_dist={total_distance:.3f} scorable_s={scorable_duration_s:.3f} filler_s={filler_duration_s:.3f} absorbed_s={absorbed_duration_s:.3f} "
                f"group_distance={dict(zip(group_names, group_distance))} group_ratios={dict(zip(group_names, [round(r, 3) for r in ratios]))}"
            )

        def try_consume_as_filler(seg: GestureSegment, current_idx: int, seg_idx_in_window: int) -> bool:
            nonlocal filler_duration_s, total_duration_s, absorbed_duration_s, absorbed_distance, total_distance

            dt = seg.duration_s
            dist = seg.path_length

            # Long idle filler breaks the window.
            if is_idle_dir(seg.direction_type) and dt > spell_definition.max_idle_gap_s:
                return False

            # Always advance wall-clock duration and window span when we consume anything.
            total_duration_s += dt
            mark_used_index(current_idx)

            # Idle segments are never absorbed into direction groups.
            if is_idle_dir(seg.direction_type):
                filler_duration_s += dt
                log_group_state("FILLER(IDLE)", seg_idx_in_window, seg, steps[step_idx])
                return True

            # Consider absorbing short, direction-adjacent jitter into a neighbouring SCORABLE step.
            if dt <= absorb_max_s:
                best_gi: int | None = None
                best_adj: int | None = None

                # Candidate A: current step if it's scorable
                cur_step = steps[step_idx]
                if not self._is_pause_step(cur_step):
                    adj = _min_adj_to_allowed(seg.direction_type, cur_step.allowed)
                    if adj is not None and adj <= absorb_adjacent_tol:
                        best_adj = adj
                        best_gi = step_to_group[step_idx]

                # Candidate B: last matched scorable step
                if last_scorable_allowed is not None and last_scorable_group_idx is not None:
                    adj = _min_adj_to_allowed(seg.direction_type, last_scorable_allowed)
                    if adj is not None and adj <= absorb_adjacent_tol:
                        if best_adj is None or adj < best_adj:
                            best_adj = adj
                            best_gi = last_scorable_group_idx

                if best_gi is not None:
                    absorbed_duration_s += dt
                    absorbed_distance += dist

                    total_distance += dist
                    group_absorbed_distance[best_gi] += dist
                    group_absorbed_duration[best_gi] += dt

                    if self._logger.isEnabledFor(logging.DEBUG):
                        self._logger.debug(
                            f"ABSORB filler: spell={self._target_spell_definition.name} win_start={i_start} seg_win_idx={seg_idx_in_window} "
                            f"dir={seg.direction_type.name} dt={dt:.3f} dist={dist:.3f} -> group={group_names[best_gi]} adj={best_adj} "
                            f"absorb_max_s={absorb_max_s:.3f} adj_tol={absorb_adjacent_tol}"
                        )
                    return True

            # Otherwise: true filler
            filler_duration_s += dt
            log_group_state("FILLER", seg_idx_in_window, seg, steps[step_idx])
            return True

        i = i_start
        while i >= 0 and step_idx < step_count:
            seg = segs[i]
            current_idx = i

            dt = seg.duration_s
            dist = seg.path_length
            step = steps[step_idx]

            seg_idx_in_window = i_start - i
            step_dirs = {d.name for d in step.allowed}

            dir_ok = seg.direction_type in step.allowed

            # Support optional SpellStep.max_duration_s if present.
            max_dur = getattr(step, "max_duration_s", None)
            dur_ok = dt >= step.min_duration_s and (max_dur is None or dt <= max_dur)

            # ─── Match branch ───────────────────────────────────────
            if dir_ok and dur_ok:
                total_duration_s += dt
                mark_used_index(current_idx)

                if self._is_pause_step(step):
                    matched_pause += 1
                    pause_duration_s += dt
                    log_group_state("MATCH(PAUSE)", seg_idx_in_window, seg, step)
                else:
                    gi = step_to_group[step_idx]

                    total_distance += dist
                    group_distance[gi] += dist

                    scorable_duration_s += dt
                    group_duration[gi] += dt

                    group_steps_matched[gi] += 1

                    if step.required:
                        matched_required += 1
                    else:
                        matched_optional += 1

                    last_scorable_allowed = step.allowed
                    last_scorable_group_idx = gi

                    log_group_state("MATCH", seg_idx_in_window, seg, step)

                step_idx += 1
                i -= 1
                continue

            # ─── Mismatch branch ────────────────────────────────────
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(
                    f"MISMATCH spell={self._target_spell_definition.name} win_start={i_start} seg_win_idx={seg_idx_in_window} "
                    f"dir={seg.direction_type.name} step_idx={step_idx}/{step_count} step_allowed={step_dirs} "
                    f"dt={dt:.3f} dist={dist:.3f} step_required={step.required} step_is_pause={self._is_pause_step(step)}"
                )

            # OPTIONAL STEP: skip it and re-check same segment against next step.
            if not step.required:
                step_idx += 1
                continue

            # REQUIRED STEP: treat as filler (possibly absorbed jitter). If we can't consume, window dies.
            if try_consume_as_filler(seg, current_idx, seg_idx_in_window):
                i -= 1
                continue

            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(
                    f"REQUIRED step failed and not filler: spell={self._target_spell_definition.name} "
                    f"seg_win_idx={seg_idx_in_window} step_idx={step_idx}"
                )
            return None

        # ─── Build metrics & run rules ───────────────────────────────────────

        used_steps_scorable = matched_required + matched_optional

        if matched_required == 0:
            return None

        if used_min_idx is None or used_max_idx is None:
            window_start_index = i_start
            window_end_index = i_start
        else:
            window_start_index = used_min_idx
            window_end_index = used_max_idx

        # chronological endpoints (segs is oldest→newest)
        start_ts = segs[window_start_index].start_ts_ms
        end_ts = segs[window_end_index].end_ts_ms

        metrics = SpellMatchMetrics(
            total_duration_s=total_duration_s,
            filler_duration_s=filler_duration_s,
            scorable_duration_s=scorable_duration_s,
            total_distance=total_distance,
            absorbed_duration_s=absorbed_duration_s,
            absorbed_distance=absorbed_distance,
            group_distance=group_distance,
            group_duration_s=group_duration,
            group_steps_matched=group_steps_matched,
            group_absorbed_distance=group_absorbed_distance,
            group_absorbed_duration_s=group_absorbed_duration,
            used_steps=used_steps_scorable,  # excludes pause steps
            total_steps=scorable_total,  # excludes pause steps
            required_matched=matched_required,
            required_total=required_total,
            optional_matched=matched_optional,
            optional_total=optional_total,
        )

        ctx = SpellMatchContext(
            spell=spell_definition,
            segments=segs,
            metrics=metrics,
            window_start_index=window_start_index,
            window_end_index=window_end_index,
        )

        if not self._rules_validator.validate(ctx):
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(
                    f"NO MATCH (rules): spell={self._target_spell_definition.name} win_start={i_start} "
                    f"required={matched_required}/{required_total} used_scorable={used_steps_scorable}/{scorable_total} "
                    f"pause_steps={matched_pause} pause_s={pause_duration_s:.3f} "
                    f"scorable_s={scorable_duration_s:.3f} filler_s={filler_duration_s:.3f} absorbed_s={absorbed_duration_s:.3f} "
                    f"total_dist={total_distance:.3f} absorbed_dist={absorbed_distance:.3f}"
                )
            return None

        accuracy = self._accuracy_scorer.calculate(spell_definition, metrics)

        if self._logger.isEnabledFor(logging.DEBUG):
            ratios = [gd / total_distance for gd in group_distance] if total_distance > 0 else [0.0 for _ in range(group_count)]
            self._logger.debug(
                f"MATCHED spell={self._target_spell_definition.name} score={accuracy.score:.3f} win_start={i_start} "
                f"required={matched_required}/{required_total} optional={matched_optional}/{optional_total} "
                f"used_scorable={used_steps_scorable}/{scorable_total} pause_steps={matched_pause} pause_s={pause_duration_s:.3f} "
                f"total_duration={total_duration_s:.3f} scorable_s={scorable_duration_s:.3f} filler_s={filler_duration_s:.3f} absorbed_s={absorbed_duration_s:.3f} "
                f"total_distance={total_distance:.3f} absorbed_dist={absorbed_distance:.3f} "
                f"group_distance={dict(zip(group_names, group_distance))} group_ratios={dict(zip(group_names, [round(r, 3) for r in ratios]))}"
            )

        return SpellMatch(
            wand_id=wand_id,
            spell_id=self._target_spell_definition.name,
            spell_name=self._target_spell_definition.name,
            start_ts_ms=start_ts,
            end_ts_ms=end_ts,
            duration_s=total_duration_s,
            segments_used=used_steps_scorable,  # excludes pause steps
            total_segments=scorable_total,  # excludes pause steps
            required_matched=matched_required,
            required_total=required_total,
            optional_matched=matched_optional,
            optional_total=optional_total,
            filler_duration_s=filler_duration_s,
            accuracy_score=accuracy.score,
        )
