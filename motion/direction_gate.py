from __future__ import annotations

import math

from gamevolt.toolkit.timer import Timer
from motion.direction_type import DirectionType


class DirectionGate:
    """
    Quantises velocity to 8-way directions and debounces commits with a dwell timer.
    """

    def __init__(self, min_dir_duration_s: float, axis_deadband_per_s: float, speed_stop: float) -> None:
        self._dir_dwell = Timer(min_dir_duration_s)
        self._axis_deadband = axis_deadband_per_s
        self._speed_stop = speed_stop

        self.current: DirectionType = DirectionType.NONE
        self.candidate: DirectionType = DirectionType.NONE

    def _pick(self, vx: float, vy: float, speed: float) -> DirectionType:
        if speed < max(self._axis_deadband, self._speed_stop):
            return DirectionType.NONE
        a = math.degrees(math.atan2(vy, vx))  # -180..180, 0=E, +90=N
        if 67.5 <= a < 112.5:
            return DirectionType.MOVING_N
        if 22.5 <= a < 67.5:
            return DirectionType.MOVING_NE
        if -22.5 <= a < 22.5:
            return DirectionType.MOVING_E
        if -67.5 <= a < -22.5:
            return DirectionType.MOVING_SE
        if -112.5 <= a < -67.5:
            return DirectionType.MOVING_S
        if -157.5 <= a < -112.5:
            return DirectionType.MOVING_SW
        if a >= 157.5 or a < -157.5:
            return DirectionType.MOVING_W
        if 112.5 <= a < 157.5:
            return DirectionType.MOVING_NW
        return DirectionType.NONE

    def update(self, vx: float, vy: float, speed: float) -> DirectionType | None:
        """
        Returns a committed new direction (or None if no change).
        """
        pick = self._pick(vx, vy, speed)
        if pick == DirectionType.NONE:
            return None

        if self.current == DirectionType.NONE:
            if self.candidate != pick:
                self.candidate = pick
                if not self._dir_dwell.is_running and not self._dir_dwell.is_complete:
                    self._dir_dwell.start()
            elif self._dir_dwell.is_complete:
                self._dir_dwell.stop()
                self.current = pick
                return self.current
        else:
            if pick != self.candidate:
                self.candidate = pick
                if not self._dir_dwell.is_running and not self._dir_dwell.is_complete:
                    self._dir_dwell.start()
            elif self._dir_dwell.is_complete and pick != self.current:
                self._dir_dwell.stop()
                self.current = pick
                return self.current
        return None

    def force(self, dir_type: DirectionType) -> None:
        """Force-impose a direction (e.g., NONE when stopping; or after commit)."""
        self.current = dir_type
        self.candidate = dir_type
        self._dir_dwell.stop()
