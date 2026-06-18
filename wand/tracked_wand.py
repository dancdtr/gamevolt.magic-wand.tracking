from __future__ import annotations

from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging._logger import Logger
import math

from motion.motion_phase_type import MotionPhaseType
from motion.motion_processor import MotionProcessor
from motion.stroke.stroke_trimmer import lead_in_cut_index, tail_cut_index
from motion.stroke.stroke_windower import Stroke, StrokeWindower
from spells.matching.dollar_one.dollar_one_recognizer import DollarOneRecognizer, Recognition
from spells.scoring.cast_attempt import CastAttempt
from spells.scoring.spell_scorer import SpellScorer
from spells.spell_cast import SpellCast
from spells.spell_type import SpellType
from wand.configuration.wand_settings import WandSettings
from wand.interpreters.wand_forward_gravity_interpreter import ForwardGravityInterpreter
from wand.wand_base import WandBase
from wand.wand_rotation import WandRotation
from wand.wand_rotation_raw import WandRotationRaw


class TrackedWand(WandBase):
    def __init__(
        self,
        logger: Logger,
        settings: WandSettings,
        id: str,
        motion_processor: MotionProcessor,
        forward_interpreter: ForwardGravityInterpreter,
        stroke_windower: StrokeWindower,
        recognizer: DollarOneRecognizer,
        scorer: SpellScorer,
    ) -> None:
        super().__init__(logger, motion_processor)

        self.spell_cast: Event[Callable[[SpellCast], None]] = Event()
        self.cast_attempted: Event[Callable[[CastAttempt], None]] = Event()
        self.motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.rotation_updated: Event[Callable[[WandRotation], None]] = Event()
        self.forward_reset: Event[Callable[[], None]] = Event()

        self._forward_interpreter = forward_interpreter
        self._motion_processor = motion_processor
        self._stroke_windower = stroke_windower
        self._recognizer = recognizer
        self._scorer = scorer
        self._settings = settings
        self._id = id

        # Zone-active spell set, as template labels (= SpellType names). Empty = score nothing.
        self._active_labels: set[str] = set()
        self._last_rotation: WandRotation | None = None
        self._is_running = False

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        self._motion_processor.motion_changed.subscribe(self._on_motion_changed)
        self._stroke_windower.stroke_completed.subscribe(self._on_stroke_completed)

        self._motion_processor.start()

        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

        self._motion_processor.stop()

        self._motion_processor.motion_changed.unsubscribe(self._on_motion_changed)
        self._stroke_windower.stroke_completed.unsubscribe(self._on_stroke_completed)

        self.reset()

    def update(self) -> None:
        pass

    def set_spell_targets(self, spell_types: list[SpellType]) -> None:
        self._logger.info(f"Wand ({self._id}) updating spell targets to '{[spell_type.name for spell_type in spell_types]}'.")
        self._active_labels = {spell_type.name for spell_type in spell_types}

    def clear_spell_target(self) -> None:
        self.set_spell_targets([])
        self._scorer.reset_streak(self._id)

    def reset(self) -> None:
        self._forward_interpreter.reset()
        self.reset_data()

    def reset_data(self) -> None:
        self._motion_processor.reset()
        self._stroke_windower.reset()
        self.forward_reset.invoke()

    def reset_forward(self) -> None:
        self._forward_interpreter.reset()

    def on_rotation_raw_updated(self, raw: WandRotationRaw) -> None:
        wand_pos = self._forward_interpreter.on_sample(raw.id, raw.ms, raw.fx, raw.fy, raw.fz)
        transformed = WandRotation(
            id=raw.id,
            ts_ms=wand_pos.ts_ms,
            x_delta=wand_pos.x_delta,
            y_delta=wand_pos.y_delta,
            nx=wand_pos.nx,
            ny=wand_pos.ny,
        )

        self._last_rotation = transformed
        self._motion_processor.on_rotation_updated(transformed)
        self._stroke_windower.on_rotation(transformed)
        self.rotation_updated.invoke(transformed)

    def _on_motion_changed(self, motion_phase: MotionPhaseType) -> None:
        self._stroke_windower.on_phase(motion_phase)

        # A sustained still (STOPPED) means the user has truly settled — reset the forward
        # interpreter so the next spell integrates from the current orientation.
        if motion_phase is MotionPhaseType.STOPPED:
            self.reset_forward()
            self.forward_reset.invoke()

        self._logger.verbose(f"Wand ({self._id}) motion: {motion_phase.name}")
        self.motion_changed.invoke(motion_phase)

    def _slice_stroke(self, stroke: Stroke, start: int, end: int) -> Stroke | None:
        points = stroke.points[start:end]
        times = stroke.times_ms[start:end]
        if len(points) < 2:
            return None

        path_length = sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)))
        return Stroke(points=points, times_ms=times, path_length=path_length)

    def _recognise_best_variant(self, stroke: Stroke) -> tuple[Stroke, list[Recognition]] | None:
        """Recognise the raw stroke plus head-, tail-, and both-trimmed variants and keep
        whichever scores highest. People draw a straight 'approach' run into the glyph and/or
        a straight 'reset' run back toward centre after it; trimming each end lets a clean
        glyph win, while a glyph that genuinely starts or ends straight matches best untrimmed
        and still wins. The combined variant covers an approach *and* a reset in one stroke."""
        n = len(stroke.points)
        head = lead_in_cut_index(stroke.points, self._settings.lead_in_trim)
        tail = tail_cut_index(stroke.points, self._settings.tail_trim)

        # Deduped (start, exclusive-end) -> label spans. The full stroke is always tried;
        # head/tail/both are added only when their trim is non-trivial and non-overlapping.
        spans: dict[tuple[int, int], str] = {(0, n): "raw"}
        if head > 0:
            spans[(head, n)] = "head"
        if tail < n:
            spans[(0, tail)] = "tail"
        if head > 0 and tail < n and head < tail:
            spans[(head, tail)] = "head+tail"

        scored: list[tuple[str, Stroke, list[Recognition]]] = []
        for (start, end), label in spans.items():
            variant = self._slice_stroke(stroke, start, end)
            if variant is None:
                continue
            results = self._recognizer.recognize(variant.points, allowed=self._active_labels)
            if results:
                scored.append((label, variant, results))
        if not scored:
            return None

        scored.sort(key=lambda lvr: lvr[2][0].score, reverse=True)
        best_label, best_stroke, best_results = scored[0]
        if len(scored) > 1:
            summary = ", ".join(
                f"{label}:{results[0].label} {results[0].score * 100:.1f}%" for label, _, results in scored
            )
            self._logger.debug(
                f"Wand ({self._id}) trim match: chose '{best_label}' "
                f"({best_stroke.point_count}/{n} pts) [{summary}]."
            )
        return best_stroke, best_results

    def _confusion_guard_usurper(self, stroke: Stroke, chosen: Recognition) -> Recognition | None:
        """The top template (scored across ALL templates, not just the active set) that beats the
        chosen spell by more than the guard margin, or None if the chosen match holds up.

        $1 absolute scores are forgiving, so a loose match can clear the gate when its true shape
        isn't an active candidate. Comparing against every template restores $1's ranking-based
        discrimination: if some inactive glyph fits the drawn shape better, the cast is a miscast."""
        guard = self._settings.confusion_guard
        if not guard.enabled:
            return None

        for r in self._recognizer.recognize(stroke.points, allowed=None):
            if r.label == chosen.label:
                continue  # the chosen spell is (one of) the global best — it holds up
            return r if r.score > chosen.score + guard.margin else None
        return None

    def _on_stroke_completed(self, stroke: Stroke) -> None:
        recognition = self._recognise_best_variant(stroke)
        if recognition is None:
            return

        stroke, results = recognition

        top = results[:3]
        candidates = ", ".join(f"{r.label} {r.score * 100:.1f}%" for r in top)

        best = results[0]
        usurper = self._confusion_guard_usurper(stroke, best)
        gate_failures = (f"confused~{usurper.label}",) if usurper is not None else ()
        if usurper is not None:
            self._logger.info(
                f"Wand ({self._id}) confusion guard rejected '{best.label}' "
                f"({best.score * 100:.1f}%): out-ranked by inactive "
                f"'{usurper.label}' ({usurper.score * 100:.1f}%)."
            )

        cast = self._scorer.score(self._id, best.label, best.score, stroke, gate_failures=gate_failures)
        self._scorer.apply_outcome(self._id, cast)

        self._logger.info(
            f"Wand ({self._id}) $1 [{candidates}] dur={stroke.duration_s:.2f}s "
            f"path={stroke.path_length:.2f} pts={stroke.point_count} -> {cast.summary()}"
        )

        # Fire for every attempt (recognised or not) so the visualiser can show rejects + breakdown.
        self.cast_attempted.invoke(
            CastAttempt(
                wand_id=self._id,
                score=cast,
                candidates=tuple(results),
                stroke_points=tuple(stroke.points),
                normalized_points=tuple(self._recognizer.prepare_points(stroke.points)),
                template_points=tuple(self._recognizer.template_points(best.label)),
                duration_s=stroke.duration_s,
                path_length=stroke.path_length,
                point_count=stroke.point_count,
            )
        )

        if not cast.recognized:
            return

        spell_type = SpellType[best.label]
        self.spell_cast.invoke(SpellCast(wand_id=self._id, spell_type=spell_type, score=cast))
