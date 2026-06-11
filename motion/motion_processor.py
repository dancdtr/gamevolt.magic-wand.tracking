import math
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

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def reset(self) -> None:
        self._phase_tracker.reset()
        self._motion_mode = MotionPhaseType.NONE
        self._previous_position = None

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
            return
        dt = raw_dt_ms / 1000.0

        vx = rotation.x_delta / dt
        vy = rotation.y_delta / dt
        speed = math.hypot(vx, vy)

        phase_update = self._phase_tracker.step(speed)
        if phase_update.new_phase is not None:
            self._set_motion_phase(phase_update.new_phase)

        self._previous_position = rotation
