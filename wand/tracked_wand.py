# tracked_wand.py
from __future__ import annotations

from logging import Logger
from typing import Callable

from gamevolt.events.event import Event
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_history import GestureHistory
from motion.gesture.gesture_segment import GestureSegment
from motion.motion_phase_type import MotionPhaseType
from motion.motion_processor import MotionProcessor
from spells.spell_matcher import SpellMatcher
from wand.configuration.wand_settings import WandSettings
from wand.interpreters.wand_yawpitch_rmf_interpreter import YawPitchRMFInterpreter
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
    ) -> None:
        super().__init__(logger, motion_processor)
        self._settings = settings

        self._motion_processor = motion_processor
        self._gesture_history = gesture_history
        self._spell_matcher = spell_matcher

        self._id = id

        self._yaw_pitch_interpreter = YawPitchRMFInterpreter(settings.rmf)

        self.direction_changed: Event[Callable[[DirectionType], None]] = Event()
        self.gesture_detected: Event[Callable[[GestureHistory], None]] = Event()
        self.motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.rotation_updated: Event[Callable[[WandRotation], None]] = Event()
        self.forward_reset: Event[Callable[[], None]] = Event()

        self._last_rotation: WandRotation | None = None

    @property
    def id(self) -> str:
        return self._id

    def start(self) -> None:
        self._motion_processor.motion_changed.subscribe(self._on_motion_changed)
        self._motion_processor.segment_completed.subscribe(self._on_segment_completed)

        self._motion_processor.start()

    def stop(self) -> None:
        self._motion_processor.stop()

        self._motion_processor.segment_completed.unsubscribe(self._on_segment_completed)
        self._motion_processor.motion_changed.unsubscribe(self._on_motion_changed)

    def update(self) -> None:
        # check lifetime timers etc
        # if self._last_rotation:
        # self._logger.info(f"Wand_{self._id} @ {self._last_rotation}")
        pass

    def reset_data(self) -> None:
        self._motion_processor.reset()
        self._gesture_history.clear()
        self.forward_reset.invoke()

    def reset_forward(self) -> None:
        self._yaw_pitch_interpreter.reset()
        # self._reset()

    def clear_gesture_history(self) -> None:
        self._gesture_history.clear()

    def on_rotation_raw_updated(self, raw: WandRotationRaw) -> None:
        wand_pos = self._yaw_pitch_interpreter.on_sample(raw.id, raw.ms, raw.yaw, raw.pitch)
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

        self._logger.debug(f"Motion: {motion_phase.name}")
        self.motion_changed.invoke(motion_phase)

    def _on_direction_changed(self, direction: DirectionType) -> None:
        self.direction_changed.invoke(direction)

    def _on_segment_completed(self, segment: GestureSegment):
        self._logger.debug(f"Completed '{segment.direction_type.name}' ({segment.direction:.3f}): {segment.duration_s}s")
        self._gesture_history.add(segment)
        self.gesture_detected.invoke(self._gesture_history)

        self._spell_matcher.try_match

        if self._spell_matcher.try_match(self.id, self._gesture_history.tail()):
            self.reset_data()
