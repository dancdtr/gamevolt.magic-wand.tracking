from __future__ import annotations

import math

from gamevolt.toolkit.timer import Timer
from motion.direction.configuration.direction_quantizer_settings import DirectionQuantizerSettings
from motion.direction.direction_type import DirectionType
from motion.direction.direction_update import DirectionUpdate


class DirectionQuantizer:
    """
    Quantises velocity to 8-way directions and debounces commits with a dwell timer.

    Notes:
      - DirectionType.UNKNOWN means "no confident direction / ignore".
      - DirectionType.PAUSE means "deliberate stillness" (emits a segment).
    """

    def __init__(self, settings: DirectionQuantizerSettings) -> None:
        self._settings = settings
        self._dir_dwell = Timer(settings.min_direction_duration)

        self._current: DirectionType = DirectionType.UNKNOWN  # last committed direction
        self._candidate: DirectionType = DirectionType.UNKNOWN  # candidate direction waiting to commit

    def step(self, vx: float, vy: float, speed: float) -> DirectionUpdate:
        pick = self._get_direction(vx, vy, speed)

        # No confident direction -> do not change state, do not emit commit
        if pick == DirectionType.UNKNOWN:
            # stop any in-flight dwell so it can't "complete" later for a stale candidate
            self._candidate = DirectionType.UNKNOWN
            self._dir_dwell.stop()
            return DirectionUpdate(None)

        # If we're definitely stopped, commit PAUSE immediately (prevents "pause" being swallowed by moving)
        if pick == DirectionType.PAUSE and speed < self._settings.speed_stop:
            if self._current != DirectionType.PAUSE:
                self._dir_dwell.stop()
                self._candidate = DirectionType.PAUSE
                self._current = DirectionType.PAUSE
                return DirectionUpdate(DirectionType.PAUSE)
            return DirectionUpdate(None)

        # Candidate changed -> restart dwell
        if pick != self._candidate:
            self._candidate = pick
            self._dir_dwell.stop()  # ensures a clean restart
            self._dir_dwell.start()
            return DirectionUpdate(None)

        # Candidate is stable; if it's already committed, nothing to do
        if self._candidate == self._current:
            self._dir_dwell.stop()
            return DirectionUpdate(None)

        # Candidate stable and dwell complete -> commit
        if self._dir_dwell.is_complete:
            self._dir_dwell.stop()
            self._current = self._candidate
            return DirectionUpdate(self._current)

        return DirectionUpdate(None)

    def force(self, dir_type: DirectionType) -> None:
        """Force-impose a direction (e.g., NONE when stopping; or after commit)."""
        self._current = dir_type
        self._candidate = dir_type
        self._dir_dwell.stop()

    def reset(self) -> None:
        self.force(DirectionType.UNKNOWN)

    def _get_direction(self, vx: float, vy: float, speed: float) -> DirectionType:
        # Stillness -> PAUSE
        if speed < self._settings.axis_deadband_per_s:
            return DirectionType.PAUSE

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

        return DirectionType.UNKNOWN
