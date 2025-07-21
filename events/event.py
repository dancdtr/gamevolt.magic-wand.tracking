import traceback
from logging import Logger
from typing import Callable, Generic, List, TypeVar

T = TypeVar("T", bound=Callable[..., None])


class Event(Generic[T]):
    def __init__(self, logger: Logger | None = None):
        self._subscribers: List[T] = []
        self._logger = logger

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def invoke(self, *args, **kwargs) -> None:
        for subscriber in self._subscribers:
            try:
                subscriber(*args, **kwargs)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error invoking subscriber {subscriber.__name__}: {e}\n{traceback.format_exc()}")
                else:
                    pass

    def subscribe(self, subscriber: T) -> None:
        self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: T) -> None:
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def unsubscribe_all(self) -> None:
        self._subscribers.clear()
