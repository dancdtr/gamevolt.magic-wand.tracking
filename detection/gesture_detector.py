from collections.abc import Callable
from logging import Logger

from detection.configuration.gesture_detector_settings import GestureDetectorSettings
from gamevolt.events.event import Event
from gamevolt.imu.sensor_data import SensorData
from gamevolt.serial.imu_binary_receiver import IMUBinaryReceiver
from gamevolt.toolkit.timer import Timer
from vector_2 import Vector2

# --- GYRO ---
# x = roll (twist around shaft)
# y = pitch (up/down)
# z = yaw (left/right)


class GestureDetector:
    def __init__(self, logger: Logger, receiver: IMUBinaryReceiver, settings: GestureDetectorSettings):
        self._logger = logger
        self._settings = settings

        self._receiver = receiver

        self._velocities: list[Vector2] = []

        self._in_motion = False
        self._end_count = 0

        self.motion_started = Event[Callable[[], None]]()
        self.motion_ended = Event[Callable[[list[Vector2]], None]]()

        self._timer = Timer(settings.min_duration)

    def start(self) -> None:
        self._receiver.data_updated.subscribe(self._on_data_updated)

    def stop(self) -> None:
        self._receiver.data_updated.unsubscribe(self._on_data_updated)

    def _on_data_updated(self, data: SensorData) -> None:
        gx, gy, gz = data.gyro.x, data.gyro.y, data.gyro.z
        mag = max(abs(gy), abs(gz))

        if not self._in_motion:
            self._velocities.append(Vector2(gz, gy))

            if mag > self._settings.start_thresh and len(self._velocities) >= self._settings.start_frames:
                self._on_motion_started()
            elif mag <= self._settings.start_thresh:
                self._velocities.clear()
                self._end_count = 0

        else:
            self._velocities.append(Vector2(gz, gy))
            if len(self._velocities) > self._settings.max_samples:
                self._velocities.pop(0)

            if mag < self._settings.end_thresh:
                self._end_count += 1
                if self._end_count >= self._settings.end_frames:
                    self._on_motion_stopped()
            else:
                self._end_count = 0

    def _on_motion_started(self) -> None:
        # self._logger.info("started!")
        self._in_motion = True
        self._timer.start()
        self.motion_started.invoke()

    def _on_motion_stopped(self) -> None:
        # self._logger.info("stopped!")
        # print(len(self._velocities))
        self._in_motion = False

        duration = self._timer.elapsed_time

        if self._timer.is_complete:
            self._logger.info(f"Gesture duration: {duration:.3f} - accept")
            self.motion_ended.invoke(self._velocities.copy())
        else:
            self._logger.info(f"Gesture duration: {duration:.3f} - reject")

        self._timer.stop()
        self._velocities.clear()
        self._end_count = 0
