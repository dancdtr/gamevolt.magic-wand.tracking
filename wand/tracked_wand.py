from __future__ import annotations

from typing import Callable

from gamevolt.events.event import Event
from gamevolt.logging._logger import Logger
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_history import GestureHistory
from motion.gesture.gesture_segment import GestureSegment
from motion.motion_phase_type import MotionPhaseType
from motion.motion_processor import MotionProcessor
from spells.spell_matcher import SpellMatcher
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
        gesture_history: GestureHistory,
        spell_matcher: SpellMatcher,
        forward_interpreter: ForwardGravityInterpreter,
    ) -> None:
        super().__init__(logger, motion_processor)

        self.spell_cast: Event[Callable[[TrackedWand, SpellType], None]] = Event()
        self.direction_changed: Event[Callable[[DirectionType], None]] = Event()
        self.gesture_detected: Event[Callable[[GestureHistory], None]] = Event()
        self.motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.rotation_updated: Event[Callable[[WandRotation], None]] = Event()
        self.forward_reset: Event[Callable[[], None]] = Event()

        self._forward_interpreter = forward_interpreter
        self._motion_processor = motion_processor
        self._gesture_history = gesture_history
        self._spell_matcher = spell_matcher
        self._settings = settings
        self._id = id

        self._current_spell_targets: list[SpellType] = []
        self._last_rotation: WandRotation | None = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        # self._motion_processor.direction_changed.subscribe(self._on_direction_changed)
        self._motion_processor.segment_completed.subscribe(self._on_segment_completed)
        self._motion_processor.motion_changed.subscribe(self._on_motion_changed)

        self._motion_processor.start()

        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

        self._motion_processor.stop()

        self._spell_matcher.clear_spell_targets()

        # self._motion_processor.direction_changed.unsubscribe(self._on_direction_changed)
        self._motion_processor.segment_completed.unsubscribe(self._on_segment_completed)
        self._motion_processor.motion_changed.unsubscribe(self._on_motion_changed)

        self.reset()

    def update(self) -> None:
        pass

    def set_spell_targets(self, spell_types: list[SpellType]) -> None:
        self._logger.info(f"Wand ({self._id}) updating spell targets to '{[spell_type.name for spell_type in spell_types]}'.")
        self._current_spell_targets = spell_types
        self._spell_matcher.set_spell_target(spell_types)

    def clear_spell_target(self) -> None:
        self.set_spell_targets([])

    def reset(self) -> None:
        self._forward_interpreter.reset()
        self.reset_data()

    def reset_data(self) -> None:
        self._motion_processor.reset()
        self._gesture_history.clear()
        self.forward_reset.invoke()

    def reset_forward(self) -> None:
        self._forward_interpreter.reset()

    def clear_gesture_history(self) -> None:
        self._gesture_history.clear()

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
        self.rotation_updated.invoke(transformed)

    def _on_motion_changed(self, motion_phase: MotionPhaseType) -> None:
        if motion_phase is MotionPhaseType.HOLDING:
            self._gesture_history.clear()

        if motion_phase is MotionPhaseType.STOPPED:
            self.forward_reset.invoke()
            self.reset_forward()

        self._logger.verbose(f"Wand ({self._id}) motion: {motion_phase.name}")
        self.motion_changed.invoke(motion_phase)

    def _on_direction_changed(self, direction: DirectionType) -> None:
        self.direction_changed.invoke(direction)

    def _on_segment_completed(self, segment: GestureSegment) -> None:
        self._logger.verbose(
            f"Wand ({self._id}) completed '{segment.direction_type.name}' ({segment.direction:.3f}): {segment.duration_s}s"
        )
        self._gesture_history.add(segment)
        self.gesture_detected.invoke(self._gesture_history)

        matched_type = self._spell_matcher.try_match(self.id, self._gesture_history.tail())
        if matched_type:
            self._logger.verbose(f"Wand ({self._id}) matched '{matched_type.name}'!")
            self.spell_cast.invoke(self, matched_type)
            self.reset_data()
