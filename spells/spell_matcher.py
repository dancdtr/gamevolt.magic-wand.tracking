# spells/spell_matcher.py
from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from logging import Logger

from gamevolt.events.event import Event
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from spells.accuracy.spell_accuracy_scorer import SpellAccuracyScorer
from spells.control.spell_controller import SpellController
from spells.library.spell_definition_factory import SpellDefinitionFactory
from spells.matching.rules.rules_validator import RulesValidator
from spells.matching.spell_match_context import SpellMatchContext
from spells.matching.spell_match_metrics import SpellMatchMetrics
from spells.spell import Spell
from spells.spell_definition import SpellDefinition
from spells.spell_match import SpellMatch
from spells.spell_step import SpellStep


class SpellMatcher:
    def __init__(
        self,
        logger: Logger,
        accuracy_scorer: SpellAccuracyScorer,
        spell_controller: SpellController,
    ) -> None:
        self._logger = logger

        self.matched: Event[Callable[[SpellMatch], None]] = Event()

        self._accuracy_scorer = accuracy_scorer
        self._rules_validator = RulesValidator()

        self._spell_controller = spell_controller
        self._spell_definition_factory = SpellDefinitionFactory()

        self._spell_definitions: list[SpellDefinition] = []

    def start(self) -> None:
        self._spell_controller.target_spell_updated.subscribe(self._on_target_spell_updated)

    def stop(self) -> None:
        self._spell_controller.target_spell_updated.unsubscribe(self._on_target_spell_updated)

    # ----- public entry point -----
    def try_match(self, wand_id: str, history: Sequence[GestureSegment]) -> bool:
        if not history:
            return False

        compressed = self._compress(history)  # oldest → newest

        for spell in self._spell_definitions:
            match = self._match_spell(wand_id, spell, compressed)
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

        Key behaviour:
          - PAUSE steps can match, but never count toward min_spell_steps/used_steps.
          - Idle-ish segments (PAUSE/UNKNOWN) can still be filler, and long idle filler breaks.
        """

        def is_idle_dir(d: DirectionType) -> bool:
            return d in (DirectionType.PAUSE, DirectionType.UNKNOWN)

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

        step_idx = 0

        total_duration = 0.0
        filler_duration = 0.0

        group_count = len(spell_definition.step_groups)
        group_distance = [0.0 for _ in range(group_count)]
        group_duration = [0.0 for _ in range(group_count)]
        group_steps_matched = [0 for _ in range(group_count)]
        total_distance = 0.0  # scorable (movement) distance only

        used_min_idx: int | None = None  # oldest used segment in window
        used_max_idx: int | None = None  # newest used segment in window

        group_names = [g.name for g in spell_definition.step_groups]

        def mark_used_index(idx: int) -> None:
            nonlocal used_min_idx, used_max_idx
            if used_min_idx is None or idx < used_min_idx:
                used_min_idx = idx
            if used_max_idx is None or idx > used_max_idx:
                used_max_idx = idx

        def log_group_state(prefix: str, seg_idx_in_window: int, seg: GestureSegment, step: SpellStep) -> None:
            if not self._logger.isEnabledFor(logging.DEBUG):
                return
            ratios = [gd / total_distance for gd in group_distance] if total_distance > 0 else [0.0 for _ in group_distance]
            self._logger.debug(
                f"{prefix} spell={self._spell_controller.target_spell.name} win_start={i_start} seg_win_idx={seg_idx_in_window} "
                f"dir={seg.direction_type.name} step_idx={step_idx}/{step_count} step_required={step.required} "
                f"step_is_pause={self._is_pause_step(step)} dist={seg.path_length:.3f} dt={seg.duration_s:.3f} "
                f"group_distance={dict(zip(group_names, group_distance))} group_ratios={dict(zip(group_names, [round(r, 3) for r in ratios]))}"
            )

        def try_consume_as_filler(seg: GestureSegment, current_idx: int, seg_idx_in_window: int) -> bool:
            nonlocal filler_duration, total_duration

            dt = seg.duration_s

            # Long idle filler breaks the window.
            if is_idle_dir(seg.direction_type) and dt > spell_definition.max_idle_gap_s:
                return False

            filler_duration += dt
            total_duration += dt

            gi_filler = step_to_group[step_idx]

            # Only add distance for non-idle filler (protects ratios from drift).
            if not is_idle_dir(seg.direction_type):
                group_distance[gi_filler] += seg.path_length

            mark_used_index(current_idx)
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
                total_duration += dt
                mark_used_index(current_idx)

                if self._is_pause_step(step):
                    matched_pause += 1
                    pause_duration_s += dt
                    log_group_state("MATCH(PAUSE)", seg_idx_in_window, seg, step)
                else:
                    total_distance += dist
                    gi = step_to_group[step_idx]
                    group_steps_matched[gi] += 1
                    group_distance[gi] += dist
                    group_duration[gi] += dt

                    if step.required:
                        matched_required += 1
                    else:
                        matched_optional += 1

                    log_group_state("MATCH", seg_idx_in_window, seg, step)

                step_idx += 1
                i -= 1
                continue

            # ─── Mismatch branch ────────────────────────────────────
            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(
                    f"MISMATCH spell={self._spell_controller.target_spell.name} win_start={i_start} seg_win_idx={seg_idx_in_window} "
                    f"dir={seg.direction_type.name} step_idx={step_idx}/{step_count} step_allowed={step_dirs} "
                    f"dt={dt:.3f} dist={dist:.3f} step_required={step.required} step_is_pause={self._is_pause_step(step)}"
                )

            # OPTIONAL STEP: skip it and re-check same segment against next step.
            if not step.required:
                step_idx += 1
                continue

            # REQUIRED STEP: try to treat this segment as filler between required steps.
            if try_consume_as_filler(seg, current_idx, seg_idx_in_window):
                i -= 1
                continue

            if self._logger.isEnabledFor(logging.DEBUG):
                self._logger.debug(
                    f"REQUIRED step failed and not filler: spell={self._spell_controller.target_spell.name} "
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
            total_duration_s=total_duration,
            filler_duration_s=filler_duration,
            total_distance=total_distance,
            group_distance=group_distance,
            group_steps_matched=group_steps_matched,
            group_duration_s=group_duration,
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
                    f"NO MATCH (rules): spell={self._spell_controller.target_spell.name} win_start={i_start} "
                    f"required={matched_required}/{required_total} used_scorable={used_steps_scorable}/{scorable_total} "
                    f"pause_matched={matched_pause} pause_s={pause_duration_s:.3f}"
                )
            return None

        accuracy = self._accuracy_scorer.calculate(spell_definition, metrics)

        if self._logger.isEnabledFor(logging.DEBUG):
            ratios = [gd / total_distance for gd in group_distance] if total_distance > 0 else [0.0 for _ in range(group_count)]
            self._logger.debug(
                f"MATCHED spell={self._spell_controller.target_spell.name} score={accuracy.score:.3f} win_start={i_start} "
                f"required={matched_required}/{required_total} optional={matched_optional}/{optional_total} "
                f"used_scorable={used_steps_scorable}/{scorable_total} pause_matched={matched_pause} pause_s={pause_duration_s:.3f} "
                f"total_duration={total_duration:.3f} total_distance={total_distance:.3f} "
                f"group_distance={dict(zip(group_names, group_distance))} group_ratios={dict(zip(group_names, [round(r, 3) for r in ratios]))} "
                f"filler_duration={filler_duration:.3f}"
            )

        print(f"dist: {total_distance:.2f}")

        return SpellMatch(
            wand_id=wand_id,
            spell_id=self._spell_controller.target_spell.code,
            spell_name=self._spell_controller.target_spell.name,
            start_ts_ms=start_ts,
            end_ts_ms=end_ts,
            duration_s=total_duration,
            segments_used=used_steps_scorable,  # excludes pause steps
            total_segments=scorable_total,  # excludes pause steps
            required_matched=matched_required,
            required_total=required_total,
            optional_matched=matched_optional,
            optional_total=optional_total,
            filler_duration_s=filler_duration,
            accuracy_score=accuracy.score,
        )

    def _on_target_spell_updated(self, spell: Spell) -> None:
        self._spell_definitions = [self._spell_definition_factory.create_spell(spell.type)]
