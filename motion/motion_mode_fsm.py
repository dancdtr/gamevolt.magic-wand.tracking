from __future__ import annotations

from gamevolt.toolkit.timer import Timer
from motion.motion_type import MotionType


class MotionModeFSM:
    def __init__(
        self,
        speed_start: float,
        speed_stop: float,
        min_state_dwell_s: float,
        min_stopped_duration_s: float,
    ) -> None:
        self.speed_start = speed_start
        self.speed_stop = speed_stop

        self._move_dwell = Timer(min_state_dwell_s)
        self._stop_timer = Timer(min_stopped_duration_s)

        self.mode: MotionType = MotionType.NONE
        self._stop_idle_open = False  # orchestrator reads this via update() return

    def reset(self) -> None:
        self.mode = MotionType.NONE
        self._move_dwell.stop()
        self._stop_timer.stop()
        self._stop_idle_open = False

    def update(self, speed: float) -> dict[str, bool]:
        """
        Step the FSM with current speed.
        Returns flags:
            {
              "to_moving": bool,
              "to_stationary": bool,
              "stop_started": bool,   # first time we drop <= speed_stop in this episode
            }
        """
        ev = {"to_moving": False, "to_stationary": False, "stop_started": False}

        if speed >= self.speed_start:
            # cancel any pending stop; clear stop-episode gate
            self._stop_timer.stop()
            self._stop_idle_open = False

            if self.mode != MotionType.MOVING:
                if self._move_dwell.is_complete:
                    self._move_dwell.stop()
                    self.mode = MotionType.MOVING
                    ev["to_moving"] = True
                elif not self._move_dwell.is_running:
                    self._move_dwell.start()
            else:
                self._move_dwell.stop()

        else:
            # below START → in band or below STOP
            self._move_dwell.stop()

            if speed <= self.speed_stop:
                if not self._stop_timer.is_running and not self._stop_timer.is_complete:
                    self._stop_timer.start()
                    # first tick of a true stop episode
                    if not self._stop_idle_open:
                        self._stop_idle_open = True
                        ev["stop_started"] = True

            # regardless of band/<=STOP, if stop elapsed -> STATIONARY
            if self._stop_timer.is_complete and self.mode != MotionType.STATIONARY:
                self._stop_timer.stop()
                self.mode = MotionType.STATIONARY
                self._stop_idle_open = False
                ev["to_stationary"] = True

        return ev
