import time


class Timer:
    def __init__(self, duration: float):
        self.duration = duration
        self._start_time: float | None = None

    def start(self) -> None:
        self._start_time = time.time()

    def stop(self) -> None:
        self._start_time = None

    def restart(self) -> None:
        self.stop()
        self.start()

    @property
    def is_running(self) -> bool:
        return self._start_time is not None and not self.is_complete

    @property
    def is_complete(self) -> bool:
        if self._start_time is None:
            return False
        return time.time() >= self._start_time + self.duration

    @property
    def elapsed_time(self) -> float | None:
        if self._start_time is None:
            return None
        elapsed = time.time() - self._start_time
        return elapsed

    @property
    def remaining_time(self) -> float | None:
        if self._start_time is None:
            return None
        remainder = self._start_time + self.duration - time.time()
        return max(remainder, 0.0)
