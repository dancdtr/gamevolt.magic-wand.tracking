from __future__ import annotations

import math

from gamevolt.toolkit.timer import Timer
from motion.direction.configuration.direction_quantizer_settings import DirectionQuantizerSettings
from motion.direction.direction_type import DirectionType
from motion.direction.direction_update import DirectionUpdate


class DirectionQuantizer:
    """
    Quantises velocity to 8-way directions and debounces commits with a dwell timer.
    """

    def __init__(self, settings: DirectionQuantizerSettings) -> None:
        self._settings = settings

        self._dir_dwell = Timer(settings.min_direction_duration)

        self._current: DirectionType = DirectionType.NONE
        self._candidate: DirectionType = DirectionType.NONE

    def step(self, vx: float, vy: float, speed: float) -> DirectionUpdate:
        pick = self._get_direction(vx, vy, speed)
        if pick == DirectionType.NONE:
            return DirectionUpdate(None)

        if self._current == DirectionType.NONE:
            if self._candidate != pick:
                self._candidate = pick
                if not self._dir_dwell.is_running and not self._dir_dwell.is_complete:
                    self._dir_dwell.start()
            elif self._dir_dwell.is_complete:
                self._dir_dwell.stop()
                self._current = pick
                return DirectionUpdate(self._current)
        else:
            if pick != self._candidate:
                self._candidate = pick
                if not self._dir_dwell.is_running and not self._dir_dwell.is_complete:
                    self._dir_dwell.start()
            elif self._dir_dwell.is_complete and pick != self._current:
                self._dir_dwell.stop()
                self._current = pick
                return DirectionUpdate(self._current)

        return DirectionUpdate(None)

    def force(self, dir_type: DirectionType) -> None:
        """Force-impose a direction (e.g., NONE when stopping; or after commit)."""
        self._current = dir_type
        self._candidate = dir_type
        self._dir_dwell.stop()

    def reset(self) -> None:
        self.force(DirectionType.NONE)
        pass

    def _get_direction(self, vx: float, vy: float, speed: float) -> DirectionType:
        if speed < max(self._settings.axis_deadband_per_s, self._settings.speed_stop):
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
