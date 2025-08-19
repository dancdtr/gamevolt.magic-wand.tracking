from collections import deque
from collections.abc import Callable
from logging import Logger

from detection.configuration.gesture_detector_settings import GestureDetectorSettings
from detection.gesture_point import GesturePoint
from gamevolt.events.event import Event
from gamevolt.imu.sensor_data import SensorData
from gamevolt.maths.vector_2 import Vector2
from gamevolt.serial.imu_binary_receiver import IMUBinaryReceiver
from gamevolt.toolkit.timer import Timer


class GestureDetector:
    def __init__(self, logger: Logger, receiver: IMUBinaryReceiver, settings: GestureDetectorSettings):
        self._logger = logger
        self._settings = settings
        self._receiver = receiver

        # For clean START: collect only a run of above-start-threshold frames
        self._run = deque(maxlen=self._settings.start_frames)

        # For clean END: buffer sub-threshold tail; only keep if motion resumes
        self._tail = deque(maxlen=self._settings.end_frames)

        self._gesture_points: list[GesturePoint] = []
        self._in_motion = False
        self._end_count = 0
        self._start_ts_ms: int | None = None
        self._last_kept_ts_ms: int | None = None  # last sample actually committed to gesture

        self.motion_started = Event[Callable[[], None]]()
        self.motion_ended = Event[Callable[[list[GesturePoint]], None]]()

        self._timer = Timer(self._settings.min_duration)

        if not (self._settings.start_thresh > self._settings.end_thresh):
            self._logger.warning("Start/End thresholds should have hysteresis (start > end).")

    def start(self) -> None:
        self._receiver.data_updated.subscribe(self._on_data_updated)

    def stop(self) -> None:
        self._receiver.data_updated.unsubscribe(self._on_data_updated)

    def _mag(self, gy: float, gz: float) -> float:
        # L2 magnitude across pitch/yaw; ignore roll
        return (gy * gy + gz * gz) ** 0.5

    def _commit_point(self, gp: GesturePoint) -> None:
        """Append a kept point to the gesture, maintaining max_samples and last-kept ts."""
        self._gesture_points.append(gp)
        self._last_kept_ts_ms = gp.timestamp
        if len(self._gesture_points) > self._settings.max_samples:
            self._gesture_points.pop(0)

    def _flush_tail_into_gesture(self) -> None:
        """We dipped below end_thresh but didn't end; keep that small dip."""
        while self._tail:
            self._commit_point(self._tail.popleft())

    def _on_data_updated(self, data: SensorData) -> None:
        gy, gz = data.gyro.y, data.gyro.z
        mag = self._mag(gy, gz)
        ts = data.timestamp_ms
        gp = GesturePoint(Vector2(gz, gy), ts)  # (x=gz, y=gy) as per your convention

        if not self._in_motion:
            # Start detection: need a clean run of start_frames above start_thresh
            if mag > self._settings.start_thresh:
                self._run.append(gp)
                if len(self._run) == self._settings.start_frames:
                    self._gesture_points = list(self._run)
                    self._run.clear()
                    self._on_motion_started(self._gesture_points[0].timestamp)
                    # we have already committed these points
                    self._last_kept_ts_ms = self._gesture_points[-1].timestamp
            else:
                self._run.clear()
            return

        # In motion -----------------------------------------------------------
        if mag >= self._settings.end_thresh:
            # We're above end threshold again: the previous dip (if any) is not a real end.
            if self._end_count:
                # Keep the small dip frames we buffered
                self._flush_tail_into_gesture()
                self._end_count = 0
            self._tail.clear()  # nothing pending
            self._commit_point(gp)
            return

        # Below end threshold: buffer into tail and count consecutive sub-threshold frames
        self._tail.append(gp)
        self._end_count += 1

        if self._end_count >= self._settings.end_frames:
            # True end: DO NOT keep the tail. Stop at the last kept sample.
            stop_ts_ms = self._last_kept_ts_ms if self._last_kept_ts_ms is not None else ts
            self._on_motion_stopped(stop_ts_ms)
            # Cleanup for next gesture
            self._tail.clear()
            self._end_count = 0

    def _on_motion_started(self, start_ts_ms: int) -> None:
        self._in_motion = True
        self._start_ts_ms = start_ts_ms
        self._end_count = 0
        self._tail.clear()
        self._timer.start()
        self.motion_started.invoke()

    def _on_motion_stopped(self, stop_ts_ms: int) -> None:
        self._in_motion = False

        duration_ms = max(0, stop_ts_ms - (self._start_ts_ms or stop_ts_ms))
        min_dur_ms = int(self._settings.min_duration * 1000.0)

        if duration_ms >= min_dur_ms:
            self._logger.info(f"Gesture duration: {duration_ms/1000.0:.3f}s - accept")
            self.motion_ended.invoke(self._gesture_points.copy())
        else:
            self._logger.info(f"Gesture duration: {duration_ms/1000.0:.3f}s - reject")

        self._timer.stop()
        self._gesture_points.clear()
        self._run.clear()
        self._tail.clear()
        self._end_count = 0
        self._start_ts_ms = None
        self._last_kept_ts_ms = None
