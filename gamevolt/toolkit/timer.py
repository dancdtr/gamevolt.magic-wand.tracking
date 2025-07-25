from time import time


class Timer:
    def __init__(self, duration: float):
        self.duration = duration
        self._is_complete = False
        self._is_enabled = False
        self._start_time = None
        self._end_time = None

    @property
    def is_running(self) -> bool:
        return self._is_enabled

    @property
    def is_complete(self) -> bool:
        return self._is_complete

    @property
    def remaining_time(self) -> float | None:
        current_time = time()
        if self._end_time is not None:
            return self._end_time - current_time

    @property
    def elapsed_time(self) -> float | None:
        current_time = time()
        if self._start_time is not None:
            return current_time - self._start_time
        else:
            return None

    def start(self):
        self._start_time = time()
        self._end_time = self._start_time + self.duration
        self._is_enabled = True

    def update(self):
        if not self._is_enabled:
            return

        end_time = self._end_time
        current_time = time()

        if end_time is not None and current_time >= end_time:
            self._is_complete = True

    def stop(self):
        self._is_complete = False
        self._is_enabled = False
        self._start_time = None
        self._end_time = None

    def restart(self):
        self.stop()
        self.start()
