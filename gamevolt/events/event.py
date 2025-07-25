import traceback
from logging import Logger
from typing import Callable, Generic, List, TypeVar

T = TypeVar("T", bound=Callable[..., None])


class Event(Generic[T]):
    def __init__(self):
        self._subscribers: List[T] = []

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def invoke(self, *args, **kwargs) -> None:
        for subscriber in self._subscribers:
            subscriber(*args, **kwargs)

    def subscribe(self, subscriber: T) -> None:
        self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: T) -> None:
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def unsubscribe_all(self) -> None:
        self._subscribers.clear()
