import math
from typing import Callable

from gamevolt.events.event import Event
from motion.configuration.motion_processor_settings import MotionProcessorSettings
from motion.direction.direction_quantizer import DirectionQuantizer
from motion.direction.direction_type import DirectionType
from motion.gesture.gesture_segment import GestureSegment
from motion.motion_phase_tracker import MotionPhaseTracker
from motion.motion_phase_type import MotionPhaseType
from motion.segment.segment_builder import SegmentBuilder
from wand.wand_rotation import WandRotation


class MotionProcessor:
    def __init__(self, settings: MotionProcessorSettings):
        self._settings = settings

        self.segment_completed: Event[Callable[[GestureSegment], None]] = Event()
        self.direction_changed: Event[Callable[[DirectionType], None]] = Event()
        self.motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()

        self._direction_quantizer = DirectionQuantizer(settings.direction_quantizer)
        self._phase_tracker = MotionPhaseTracker(settings.phase_tracker)
        self._segment_builder = SegmentBuilder(settings.segment_builder)

        self._motion_mode: MotionPhaseType = MotionPhaseType.NONE
        self._motion_state: DirectionType = DirectionType.NONE
        self._previous_position: WandRotation | None = None

    def start(self) -> None:
        self._segment_builder.segment_completed.subscribe(self._on_segment_completed)

    def stop(self) -> None:
        self._segment_builder.segment_completed.unsubscribe(self._on_segment_completed)

    def reset(self) -> None:
        self._phase_tracker.reset()
        self._direction_quantizer.reset()
        self._segment_builder.reset()  # WHY DID I COMMENT THIS OUT?

        self._motion_mode = MotionPhaseType.NONE
        self._motion_state = DirectionType.NONE
        self._previous_position = None

    def _set_motion_phase(self, phase: MotionPhaseType) -> None:
        if phase != self._motion_mode:
            self._motion_mode = phase
            self.motion_changed.invoke(phase)

    def _set_direction(self, dir_type: DirectionType, pos: WandRotation) -> None:
        if dir_type != self._motion_state:
            self._motion_state = dir_type
            self.direction_changed.invoke(dir_type)
            self._segment_builder.commit(dir_type, pos)

    def _on_segment_completed(self, seg) -> None:
        self.segment_completed.invoke(seg)

    def on_rotation_updated(self, rotation: WandRotation) -> None:
        if self._previous_position is None:
            self._previous_position = rotation

            self._set_motion_phase(MotionPhaseType.PAUSED)
            self._segment_builder.start(DirectionType.NONE, rotation)
            return

        raw_dt_ms = rotation.ts_ms - self._previous_position.ts_ms
        if raw_dt_ms <= 0:
            return
        dt = raw_dt_ms / 1000.0

        vx = rotation.x_delta / dt
        vy = rotation.y_delta / dt
        speed = math.hypot(vx, vy)

        phase_update = self._phase_tracker.step(speed)

        if phase_update.new_phase is not None:
            if phase_update.new_phase == MotionPhaseType.PAUSED:
                if self._motion_state != DirectionType.NONE:
                    self._set_direction(DirectionType.NONE, rotation)

            self._set_motion_phase(phase_update.new_phase)

        if self._motion_mode == MotionPhaseType.MOVING:
            direction_update = self._direction_quantizer.step(vx, vy, speed)
            if direction_update.new_direction is not None:
                self._set_direction(direction_update.new_direction, rotation)
        else:
            self._direction_quantizer.force(DirectionType.NONE)

        if self._segment_builder.active:
            self._segment_builder.accumulate(rotation)

        self._previous_position = rotation
