from __future__ import annotations

from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging._logger import Logger
import math

from motion.motion_phase_type import MotionPhaseType
from motion.motion_processor import MotionProcessor
from motion.stroke.lead_in_trimmer import lead_in_cut_index
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

    def _trim_lead_in(self, stroke: Stroke) -> Stroke:
        cut = lead_in_cut_index(stroke.points, self._settings.lead_in_trim)
        if cut <= 0:
            return stroke

        points = stroke.points[cut:]
        times = stroke.times_ms[cut:]
        if len(points) < 2:
            return stroke

        path_length = sum(math.dist(points[i - 1], points[i]) for i in range(1, len(points)))
        return Stroke(points=points, times_ms=times, path_length=path_length)

    def _recognise_best_variant(self, stroke: Stroke) -> tuple[Stroke, list[Recognition]] | None:
        """Recognise both the raw stroke and a lead-in-trimmed variant and keep whichever
        scores higher. Avoids the trade-off of always trimming: a glyph that genuinely
        starts with a straight run matches better untrimmed and wins, while a real
        approach-into-glyph matches better trimmed."""
        trimmed = self._trim_lead_in(stroke)
        variants = [stroke] if trimmed is stroke else [stroke, trimmed]

        scored: list[tuple[Stroke, list[Recognition]]] = []
        for variant in variants:
            results = self._recognizer.recognize(variant.points, allowed=self._active_labels)
            if results:
                scored.append((variant, results))
        if not scored:
            return None

        scored.sort(key=lambda vr: vr[1][0].score, reverse=True)
        best = scored[0]
        if len(scored) == 2:
            chosen = "trimmed" if best[0] is trimmed else "untrimmed"
            self._logger.debug(
                f"Wand ({self._id}) lead-in match: chose {chosen} "
                f"({best[1][0].label} {best[1][0].score * 100:.1f}% vs {scored[1][1][0].score * 100:.1f}%; "
                f"{stroke.point_count} -> {trimmed.point_count} pts)."
            )
        return best

    def _on_stroke_completed(self, stroke: Stroke) -> None:
        recognition = self._recognise_best_variant(stroke)
        if recognition is None:
            return

        stroke, results = recognition

        top = results[:3]
        candidates = ", ".join(f"{r.label} {r.score * 100:.1f}%" for r in top)

        best = results[0]
        cast = self._scorer.score(self._id, best.label, best.score, stroke)
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
