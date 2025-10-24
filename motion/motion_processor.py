from __future__ import annotations

import math
from typing import Callable

from gamevolt.events.event import Event
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from motion.direction_gate import DirectionGate
from motion.direction_type import DirectionType
from motion.motion_mode_fsm import MotionModeFSM
from motion.motion_type import MotionType
from motion.segment_builder import SegmentBuilder

_SPEED_START: float = 0.50
_SPEED_STOP: float = 0.20
_MIN_STATE_DURATION_S: float = 0.03
_MIN_DIR_DURATION_S: float = 0.03
_AXIS_DEADBAND_PER_S: float = 0.10
_MIN_STOPPED_DURATION_S: float = 0.3
_MAX_SEGMENT_POINTS: int = 256


class MotionProcessor:
    def __init__(self, input: MotionInputBase):
        self._input = input

        self.state_changed: Event[Callable[[DirectionType], None]] = Event()
        self.motion_changed: Event[Callable[[MotionType], None]] = Event()
        self.segment_completed: Event[Callable[[...], None]] = Event()  # type: ignore[typeddict]

        # Components
        self._fsm = MotionModeFSM(_SPEED_START, _SPEED_STOP, _MIN_STATE_DURATION_S, _MIN_STOPPED_DURATION_S)
        self._dir = DirectionGate(_MIN_DIR_DURATION_S, _AXIS_DEADBAND_PER_S, _SPEED_STOP)
        self._seg = SegmentBuilder(_MAX_SEGMENT_POINTS)
        self._seg.segment_completed.subscribe(self._on_segment_completed)

        # State
        self._motion_mode: MotionType = MotionType.NONE
        self._motion_state: DirectionType = DirectionType.NONE
        self._prev: WandPosition | None = None

    # lifecycle
    def start(self) -> None:
        self._input.position_updated.subscribe(self._on_position)

    def stop(self) -> None:
        self._input.position_updated.unsubscribe(self._on_position)

    # event relay
    def _on_segment_completed(self, seg) -> None:
        self.segment_completed.invoke(seg)

    def _set_motion(self, mode: MotionType) -> None:
        if mode != self._motion_mode:
            self._motion_mode = mode
            self.motion_changed.invoke(mode)

    def _set_direction(self, dir_type: DirectionType, pos: WandPosition) -> None:
        if dir_type != self._motion_state:
            self._motion_state = dir_type
            self.state_changed.invoke(dir_type)
            self._seg.commit(dir_type, pos)

    # tick
    def _on_position(self, pos: WandPosition) -> None:
        if self._prev is None:
            self._prev = pos
            # initialise in STATIONARY with idle segment
            self._set_motion(MotionType.STATIONARY)
            self._seg.start(DirectionType.NONE, pos)
            return

        # NOTE: if two samples share the same timestamp, we treat dt as tiny to avoid div-by-zero.
        raw_dt_ms = pos.ts_ms - self._prev.ts_ms
        if raw_dt_ms <= 0:
            # Optionally: drop the sample instead of clamping.
            # return
            raw_dt_ms = 1  # 1 ms fallback
        dt = raw_dt_ms / 1000.0

        vx = pos.x_delta / dt
        vy = pos.y_delta / dt
        speed = math.hypot(vx, vy)

        # 1) Mode FSM
        ev = self._fsm.update(speed)
        if ev["stop_started"]:
            if self._motion_state != DirectionType.NONE:
                self._set_direction(DirectionType.NONE, pos)
        if ev["to_stationary"]:
            self._set_motion(MotionType.STATIONARY)
        if ev["to_moving"]:
            self._set_motion(MotionType.MOVING)

        # 2) Direction while MOVING
        if self._motion_mode == MotionType.MOVING:
            committed = self._dir.update(vx, vy, speed)
            if committed is not None:
                self._set_direction(committed, pos)
        else:
            self._dir.force(DirectionType.NONE)

        # 3) Accumulate segment metrics
        if self._seg.active:
            self._seg.accumulate(pos)

        self._prev = pos
