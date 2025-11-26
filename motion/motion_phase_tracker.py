from __future__ import annotations

from gamevolt.toolkit.timer import Timer
from motion.configuration.motion_phase_tracker_settings import MotionPhaseTrackerSettings
from motion.motion_phase_update import MotionPhaseUpdate
from motion.motion_type import MotionPhaseType


class MotionPhaseTracker:
    def __init__(self, settings: MotionPhaseTrackerSettings) -> None:
        self._settings = settings

        self._move_dwell = Timer(settings.min_state_duration)
        self._stop_timer = Timer(settings.min_stopped_duration)

        self._state: MotionPhaseType = MotionPhaseType.NONE
        self._stop_idle_open = False

    def reset(self) -> None:
        self._state = MotionPhaseType.NONE
        self._move_dwell.stop()
        self._stop_timer.stop()
        self._stop_idle_open = False

    def step(self, speed: float) -> MotionPhaseUpdate:
        """
        Advance the tracker with the current speed.

        Returns a MotionPhaseUpdate describing:
        - whether the phase changed this tick
        - whether a new stop episode just began
        """
        prev_state = self._state
        stop_started = False

        if speed >= self._settings.speed_start:
            # cancel any pending stop; clear stop-episode gate
            self._stop_timer.stop()
            self._stop_idle_open = False

            if self._state != MotionPhaseType.MOVING:
                if self._move_dwell.is_complete:
                    self._move_dwell.stop()
                    self._state = MotionPhaseType.MOVING
                elif not self._move_dwell.is_running:
                    self._move_dwell.start()
            else:
                # already moving; keep dwell cleared
                self._move_dwell.stop()

        else:
            # below START → in band or below STOP
            self._move_dwell.stop()

            if speed <= self._settings.speed_stop:
                if not self._stop_timer.is_running and not self._stop_timer.is_complete:
                    self._stop_timer.start()
                    # first tick of a true stop episode
                    if not self._stop_idle_open:
                        self._stop_idle_open = True
                        stop_started = True

            # regardless of band/<=STOP, if stop elapsed -> STATIONARY
            if self._stop_timer.is_complete and self._state != MotionPhaseType.STATIONARY:
                self._stop_timer.stop()
                self._state = MotionPhaseType.STATIONARY
                self._stop_idle_open = False

        new_phase = self._state if self._state != prev_state else None
        return MotionPhaseUpdate(new_phase=new_phase, stop_started=stop_started)
