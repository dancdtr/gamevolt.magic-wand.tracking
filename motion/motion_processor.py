from __future__ import annotations

import math
from typing import Callable

from gamevolt.events.event import Event
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from motion.configuration.direction_quantizer_settings import DirectionQuantizerSettings
from motion.configuration.motion_processor_settings import MotionProcessorSettings
from motion.direction_quantizer import DirectionQuantizer
from motion.direction_type import DirectionType
from motion.motion_phase_tracker import MotionPhaseTracker
from motion.motion_type import MotionPhaseType
from motion.segment_builder import SegmentBuilder

_SPEED_STOP: float = 0.20
_MIN_DIR_DURATION_S: float = 0.03
_AXIS_DEADBAND_PER_S: float = 0.10
_MAX_SEGMENT_POINTS: int = 256
# quantizer_settings = DirectionQuantizerSettings(
#     speed_stop=_SPEED_STOP,
#     min_direction_duration=_MIN_DIR_DURATION_S,
#     axis_deadband_per_s=_AXIS_DEADBAND_PER_S,
# )


class MotionProcessor:
    def __init__(self, settings: MotionProcessorSettings, input: MotionInputBase):
        self._settings = settings
        self._input = input

        self.direction_changed: Event[Callable[[DirectionType], None]] = Event()
        self.motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()
        self.segment_completed: Event[Callable[[...], None]] = Event()  # type: ignore[typeddict]

        # Components
        self._phase_tracker = MotionPhaseTracker(settings.phase_tracker)
        self._dir = DirectionQuantizer(settings.direction_quantizer)
        self._seg = SegmentBuilder(_MAX_SEGMENT_POINTS)
        self._seg.segment_completed.subscribe(self._on_segment_completed)

        # State
        self._motion_mode: MotionPhaseType = MotionPhaseType.NONE
        self._motion_state: DirectionType = DirectionType.NONE
        self._prev: WandPosition | None = None

    # lifecycle
    def start(self) -> None:
        self._input.position_updated.subscribe(self._on_position)

    def stop(self) -> None:
        self._input.position_updated.unsubscribe(self._on_position)

    def reset(self) -> None:
        print("resetting")
        self._phase_tracker.reset()
        self._dir.reset()
        # reset self._seg?

    # event relay
    def _on_segment_completed(self, seg) -> None:
        self.segment_completed.invoke(seg)

    def _set_motion_phase(self, phase: MotionPhaseType) -> None:
        if phase != self._motion_mode:
            self._motion_mode = phase
            self.motion_changed.invoke(phase)

    def _set_direction(self, dir_type: DirectionType, pos: WandPosition) -> None:
        if dir_type != self._motion_state:
            self._motion_state = dir_type
            self.direction_changed.invoke(dir_type)
            self._seg.commit(dir_type, pos)

    def _on_position(self, pos: WandPosition) -> None:
        if self._prev is None:
            self._prev = pos
            # initialise in STATIONARY with idle segment
            self._set_motion_phase(MotionPhaseType.STATIONARY)
            self._seg.start(DirectionType.NONE, pos)
            return

        raw_dt_ms = pos.ts_ms - self._prev.ts_ms
        if raw_dt_ms <= 0:
            return
        dt = raw_dt_ms / 1000.0

        vx = pos.x_delta / dt
        vy = pos.y_delta / dt
        speed = math.hypot(vx, vy)

        phase_update = self._phase_tracker.step(speed)

        if phase_update.new_phase is not None:
            self._set_motion_phase(phase_update.new_phase)

            if phase_update.new_phase == MotionPhaseType.STATIONARY:
                self._set_direction(DirectionType.NONE, pos)

        # if phase_update.stop_started:
        # pass

        # 2) Direction while MOVING
        if self._motion_mode == MotionPhaseType.MOVING:
            direction_update = self._dir.step(vx, vy, speed)
            if direction_update.new_direction is not None:
                self._set_direction(direction_update.new_direction, pos)
        else:
            self._dir.force(DirectionType.NONE)

        # 3) Accumulate segment metrics
        if self._seg.active:
            self._seg.accumulate(pos)

        self._prev = pos
