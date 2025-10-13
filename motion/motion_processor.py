# motion_processor.py
from __future__ import annotations

import math
from collections import deque
from typing import Callable

from gamevolt.events.event import Event
from gamevolt.toolkit.timer import Timer
from input.motion_input_base import MotionInputBase
from input.wand_position import WandPosition
from motion.direction_type import DirectionType
from motion.gesture_segment import GestureSegment
from motion.motion_processor_settings import MotionProcessorSettings
from motion.motion_type import MotionType


class MotionProcessor:
    def __init__(self, input: MotionInputBase, settings: MotionProcessorSettings):
        self._settings = settings
        self._input = input

        self.state_changed: Event[Callable[[DirectionType], None]] = Event()
        self.segment_completed: Event[Callable[[GestureSegment], None]] = Event()

        self._previous_position: WandPosition | None = None
        self._motion_state: DirectionType = DirectionType.NONE
        self._candidate_state: DirectionType = DirectionType.NONE

        self._motion_timer = Timer(self._settings.min_state_duration_s)
        self._dir_timer = Timer(self._settings.min_dir_duration_s)

        # --- segment bookkeeping (full metrics + capped raw buffer) ---
        self._seg_active: bool = False
        self._seg_dir: DirectionType = DirectionType.NONE
        self._seg_origin_ts_ms: int = 0  # never changes within the segment
        self._seg_last_ts_ms: int = 0
        self._seg_total_samples: int = 0  # counts all steps seen in the segment
        self._seg_net_dx: float = 0.0
        self._seg_net_dy: float = 0.0
        self._seg_path_len: float = 0.0

        # capped raw buffer (recent points only)
        self._seg_points: deque[WandPosition] = deque(maxlen=self._settings.max_segment_points)

    def start(self) -> None:
        self._input.position_updated.subscribe(self._on_position)

    def stop(self) -> None:
        self._input.position_updated.unsubscribe(self._on_position)

    # ---------------- core ----------------

    def _on_position(self, position: WandPosition) -> None:
        if self._previous_position is None:
            self._previous_position = position
            return

        dt_s = max((position.ts_ms - self._previous_position.ts_ms) / 1000.0, 1e-6)
        vx = (position.x - self._previous_position.x) / dt_s
        vy = (position.y - self._previous_position.y) / dt_s
        speed = math.hypot(vx, vy)

        # Motion vs Stationary candidate
        if speed >= self._settings.speed_start:
            motion_candidate = MotionType.MOVING
        elif speed <= self._settings.speed_stop:
            motion_candidate = MotionType.STATIONARY
        else:
            motion_candidate = MotionType.NONE  # hysteresis gap

        if motion_candidate is not None:
            current_motion = MotionType.STATIONARY if self._candidate_state == DirectionType.NONE else MotionType.MOVING
            if motion_candidate != current_motion:
                self._motion_timer.start()
                if motion_candidate == MotionType.STATIONARY:
                    self._candidate_state = DirectionType.NONE
            elif self._motion_timer.is_complete:
                self._motion_timer.stop()
                if motion_candidate == MotionType.STATIONARY:
                    self._commit_state(DirectionType.NONE, position)
                    self._dir_timer.stop()
                # else: wait for direction commit

        # Direction candidate
        dir_candidate = self._pick_direction(vx, vy, speed)

        if dir_candidate != DirectionType.NONE:
            if self._motion_state == DirectionType.NONE:
                if self._candidate_state != dir_candidate:
                    self._candidate_state = dir_candidate
                    self._dir_timer.start()
                elif self._dir_timer.is_complete:
                    self._dir_timer.stop()
                    self._commit_state(dir_candidate, position)
            else:
                if dir_candidate != self._candidate_state:
                    self._candidate_state = dir_candidate
                    self._dir_timer.start()
                elif self._dir_timer.is_complete and dir_candidate != self._motion_state:
                    self._dir_timer.stop()
                    self._commit_state(dir_candidate, position)

        # --- segment accumulation ---
        if self._seg_active:
            # update end time first (even if we drop points, we keep full duration)
            self._seg_last_ts_ms = position.ts_ms

            # full metrics (NEVER reduced by buffer cap)
            dx = position.x - self._previous_position.x
            dy = position.y - self._previous_position.y
            self._seg_net_dx += dx
            self._seg_net_dy += dy
            self._seg_path_len += math.hypot(dx, dy)
            self._seg_total_samples += 1

            # recent raw points buffer (capped)
            self._seg_points.append(position)

        self._previous_position = position

    def _pick_direction(self, vx: float, vy: float, speed: float) -> DirectionType:
        if speed < max(self._settings.axis_deadband_per_s, self._settings.speed_stop):
            return DirectionType.NONE

        angle_deg = math.degrees(math.atan2(vy, vx))  # -180..180, 0=E, +90=N

        if 67.5 <= angle_deg < 112.5:
            return DirectionType.MOVING_N
        elif 22.5 <= angle_deg < 67.5:
            return DirectionType.MOVING_NE
        elif -22.5 <= angle_deg < 22.5:
            return DirectionType.MOVING_E
        elif -67.5 <= angle_deg < -22.5:
            return DirectionType.MOVING_SE
        elif -112.5 <= angle_deg < -67.5:
            return DirectionType.MOVING_S
        elif -157.5 <= angle_deg < -112.5:
            return DirectionType.MOVING_SW
        elif angle_deg >= 157.5 or angle_deg < -157.5:
            return DirectionType.MOVING_W
        elif 112.5 <= angle_deg < 157.5:
            return DirectionType.MOVING_NW
        else:
            return DirectionType.NONE  # very rare fallback

    # -------------- segments --------------

    def _start_segment(self, state: DirectionType, pos: WandPosition) -> None:
        self._seg_active = True
        self._seg_dir = state
        self._seg_origin_ts_ms = pos.ts_ms  # preserve true start
        self._seg_last_ts_ms = pos.ts_ms
        self._seg_total_samples = 0
        self._seg_net_dx = 0.0
        self._seg_net_dy = 0.0
        self._seg_path_len = 0.0
        self._seg_points = deque(maxlen=self._settings.max_segment_points)
        self._seg_points.append(pos)  # keep the first point for context if desired

    def _finish_segment(self) -> None:
        if not self._seg_active:
            return

        duration_s = max((self._seg_last_ts_ms - self._seg_origin_ts_ms) / 1000.0, 0.0)
        net_dx, net_dy = self._seg_net_dx, self._seg_net_dy
        mag = math.hypot(net_dx, net_dy)
        avg_vx = (net_dx / mag) if mag > 0 else 0.0
        avg_vy = (net_dy / mag) if mag > 0 else 0.0

        path_length = self._seg_path_len
        mean_speed = (path_length / duration_s) if duration_s > 0 else 0.0

        seg = GestureSegment(
            start_ts_ms=self._seg_origin_ts_ms,
            end_ts_ms=self._seg_last_ts_ms,
            duration_s=duration_s,
            sample_count=self._seg_total_samples,
            direction_type=self._seg_dir,
            avg_vec_x=avg_vx,
            avg_vec_y=avg_vy,
            net_dx=net_dx,
            net_dy=net_dy,
            mean_speed=mean_speed,
            path_length=path_length,  # ← NEW
        )
        self.segment_completed.invoke(seg)
        self._seg_active = False

    # -------------- committing --------------

    def _commit_state(self, new_state: DirectionType, pos: WandPosition) -> None:
        # close current segment (moving or NONE)
        if self._seg_active:
            self._seg_last_ts_ms = pos.ts_ms
            self._finish_segment()

        # publish state change
        if new_state != self._motion_state:
            self._motion_state = new_state
            self.state_changed.invoke(self._motion_state)

        # always start a new segment (including NONE), so idle has duration too
        self._start_segment(new_state, pos)
