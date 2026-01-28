from __future__ import annotations

from gamevolt.toolkit.timer import Timer
from motion.configuration.motion_phase_tracker_settings import MotionPhaseTrackerSettings
from motion.motion_phase_type import MotionPhaseType
from motion.motion_phase_update import MotionPhaseUpdate


class MotionPhaseTracker:
    def __init__(self, settings: MotionPhaseTrackerSettings) -> None:
        self._settings = settings

        self._move_dwell = Timer(settings.min_state_duration)

        # thresholds since still-episode start
        self._pause_timer = Timer(settings.min_paused_duration)
        self._hold_timer = Timer(settings.min_holding_duration)
        self._stop_timer = Timer(settings.min_stopped_duration)

        self._state: MotionPhaseType = MotionPhaseType.NONE
        self._still_episode_open = False

        if not (settings.min_paused_duration < settings.min_holding_duration < settings.min_stopped_duration):
            raise ValueError("Expected: min_paused_duration < min_holding_duration < min_stopped_duration")

    def reset(self) -> None:
        self._state = MotionPhaseType.NONE
        self._move_dwell.stop()
        self._pause_timer.stop()
        self._hold_timer.stop()
        self._stop_timer.stop()
        self._still_episode_open = False

    def step(self, speed: float) -> MotionPhaseUpdate:
        prev_state = self._state
        stop_started = False  # still-episode started

        # ----------------------------
        # MOVEMENT (>= START threshold)
        # ----------------------------
        if speed >= self._settings.speed_start:
            # end still episode + clear timers
            self._pause_timer.stop()
            self._hold_timer.stop()
            self._stop_timer.stop()
            self._still_episode_open = False

            if self._state != MotionPhaseType.MOVING:
                if self._move_dwell.is_complete:
                    self._move_dwell.stop()
                    self._state = MotionPhaseType.MOVING
                elif not self._move_dwell.is_running:
                    self._move_dwell.start()
            else:
                self._move_dwell.stop()

        # ---------------------------------------
        # NOT MOVING ENOUGH (< START threshold)
        # ---------------------------------------
        else:
            self._move_dwell.stop()

            # still episode begins when we fall to/below STOP threshold
            if speed <= self._settings.speed_stop:
                if not self._still_episode_open:
                    self._still_episode_open = True
                    stop_started = True

                    self._pause_timer.stop()
                    self._hold_timer.stop()
                    self._stop_timer.stop()

                    self._pause_timer.start()
                    self._hold_timer.start()
                    self._stop_timer.start()

            # while still episode is open, timers may elapse even in the band
            if self._still_episode_open:
                # Advance at most ONE state per tick (prevents skipping events)
                if self._state in (MotionPhaseType.MOVING, MotionPhaseType.NONE):
                    if self._pause_timer.is_complete:
                        self._pause_timer.stop()
                        self._state = MotionPhaseType.PAUSED

                elif self._state == MotionPhaseType.PAUSED:
                    if self._hold_timer.is_complete:
                        self._hold_timer.stop()
                        self._state = MotionPhaseType.HOLDING

                elif self._state == MotionPhaseType.HOLDING:
                    if self._stop_timer.is_complete:
                        self._stop_timer.stop()
                        self._state = MotionPhaseType.STOPPED

                # If you ever enter the still episode from NONE and the pause timer
                # hasn't elapsed yet, you’ll remain NONE until PAUSED triggers.

        new_phase = self._state if self._state != prev_state else None
        return MotionPhaseUpdate(new_phase=new_phase, stop_started=stop_started)
