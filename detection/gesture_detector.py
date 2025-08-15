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

        # Buffer only the current "run" of above-threshold frames
        self._run = deque(maxlen=self._settings.start_frames)

        self._gesture_points: list[GesturePoint] = []
        self._in_motion = False
        self._end_count = 0
        self._start_ts_ms: int | None = None

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

    def _on_data_updated(self, data: SensorData) -> None:
        gy, gz = data.gyro.y, data.gyro.z
        mag = self._mag(gy, gz)
        ts = data.timestamp_ms
        gp = GesturePoint(Vector2(gz, gy), ts)

        if not self._in_motion:
            # Only collect frames that are *currently* above start threshold
            if mag > self._settings.start_thresh:
                self._run.append(gp)
                if len(self._run) == self._settings.start_frames:
                    # Start! Seed gesture with exactly these frames
                    self._gesture_points = list(self._run)
                    self._run.clear()
                    self._on_motion_started(self._gesture_points[0].timestamp)
            else:
                # Any drop resets the run
                self._run.clear()

        else:
            # Record all samples while in motion
            self._gesture_points.append(gp)
            if len(self._gesture_points) > self._settings.max_samples:
                self._gesture_points.pop(0)

            # End logic with consecutive frames below end_thresh
            if mag < self._settings.end_thresh:
                self._end_count += 1
                if self._end_count >= self._settings.end_frames:
                    self._on_motion_stopped(ts)
            else:
                self._end_count = 0

    def _on_motion_started(self, start_ts_ms: int) -> None:
        self._in_motion = True
        self._start_ts_ms = start_ts_ms
        self._end_count = 0
        self._timer.start()
        self.motion_started.invoke()

    def _on_motion_stopped(self, stop_ts_ms: float) -> None:
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
        self._end_count = 0
        self._start_ts_ms = None
