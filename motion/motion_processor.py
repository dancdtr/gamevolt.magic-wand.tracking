import math
from collections import deque
from typing import Callable

from gamevolt.events.event import Event
from motion.configuration.motion_processor_settings import MotionProcessorSettings
from motion.motion_phase_tracker import MotionPhaseTracker
from motion.motion_phase_type import MotionPhaseType
from wand.wand_rotation import WandRotation


class MotionProcessor:
    """Derives motion phase (MOVING / PAUSED / HOLDING / STOPPED) from the rotation stream.

    Direction quantisation and segment building were removed with the legacy matcher; the
    $1 path consumes the raw point stream directly and only needs the phase signal to window
    strokes (see StrokeWindower).
    """

    def __init__(self, settings: MotionProcessorSettings):
        self._settings = settings

        self.motion_changed: Event[Callable[[MotionPhaseType], None]] = Event()

        self._phase_tracker = MotionPhaseTracker(settings.phase_tracker)
        self._motion_mode: MotionPhaseType = MotionPhaseType.NONE
        self._previous_position: WandRotation | None = None
        self._smoothed_speed: float | None = None

        # Sliding window of integrated 2D path points (ts_ms, x, y) for the spatial deadzone.
        self._path_x = 0.0
        self._path_y = 0.0
        self._recent_points: deque[tuple[int, float, float]] = deque()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def reset(self) -> None:
        self._phase_tracker.reset()
        self._motion_mode = MotionPhaseType.NONE
        self._previous_position = None
        self._smoothed_speed = None
        self._path_x = 0.0
        self._path_y = 0.0
        self._recent_points.clear()

    def _set_motion_phase(self, phase: MotionPhaseType) -> None:
        if phase != self._motion_mode:
            self._motion_mode = phase
            self.motion_changed.invoke(phase)

    def on_rotation_updated(self, rotation: WandRotation) -> None:
        if self._previous_position is None:
            self._previous_position = rotation
            self._set_motion_phase(MotionPhaseType.PAUSED)
            return

        raw_dt_ms = rotation.ts_ms - self._previous_position.ts_ms
        if raw_dt_ms <= 0:
            # Non-advancing timestamp. A wand reboot resets the tag tick counter, so
            # ts_ms jumps backwards by the whole pre-reboot run; without re-baselining
            # here every subsequent sample stays <= the stale previous and is dropped
            # forever (phase never updates, no strokes). Re-anchor on the new sample.
            self._previous_position = rotation
            return
        dt = raw_dt_ms / 1000.0

        vx = rotation.x_delta / dt
        vy = rotation.y_delta / dt
        speed = math.hypot(vx, vy)

        # EMA low-pass: suppress high-frequency hand tremor so a held wand reads as still.
        alpha = self._settings.speed_smoothing_alpha
        if self._smoothed_speed is None:
            self._smoothed_speed = speed
        else:
            self._smoothed_speed += alpha * (speed - self._smoothed_speed)
        speed = self._smoothed_speed

        # Spatial deadzone: if the recent integrated path stays within a small radius, the
        # wand is effectively held — force speed to 0 so the still-episode opens despite any
        # residual tremor velocity.
        if self._is_within_deadzone(rotation):
            speed = 0.0

        phase_update = self._phase_tracker.step(speed)
        if phase_update.new_phase is not None:
            self._set_motion_phase(phase_update.new_phase)

        self._previous_position = rotation

    def _is_within_deadzone(self, rotation: WandRotation) -> bool:
        radius = self._settings.stillness_radius
        if radius <= 0.0:
            return False

        self._path_x += rotation.x_delta
        self._path_y += rotation.y_delta
        self._recent_points.append((rotation.ts_ms, self._path_x, self._path_y))

        window_start = rotation.ts_ms - self._settings.stillness_window_ms
        while len(self._recent_points) > 1 and self._recent_points[0][0] < window_start:
            self._recent_points.popleft()

        # Need a full window of history before trusting the deadzone, else a single sample
        # at spell start would read as "still".
        if self._recent_points[0][0] > window_start:
            return False

        # Max excursion of any point in the window from the current point.
        return all(math.dist((px, py), (self._path_x, self._path_y)) <= radius for _, px, py in self._recent_points)
