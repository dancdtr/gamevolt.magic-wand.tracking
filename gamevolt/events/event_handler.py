from abc import ABC, abstractmethod
from logging import Logger
from typing import Callable, Generic, TypeVar

from gamevolt.events.event import Event

TEvent = TypeVar("TEvent")
TCallable = TypeVar("TCallable", bound=Callable)


class EventHandler(Generic[TEvent, TCallable], ABC):
    def __init__(self, logger: Logger) -> None:
        self._subscriptions: dict[TEvent, Event[TCallable]] = {}
        self._logger = logger

    def notify(self, key: TEvent, *args, **kwargs) -> None:
        if key in self._subscriptions:
            self._subscriptions[key].invoke(*args, **kwargs)

    def subscribe(self, key: TEvent, callback: TCallable) -> None:
        if key not in self._subscriptions:
            self._subscriptions[key] = Event[TCallable]()

        self._subscriptions[key].subscribe(callback)

    def unsubscribe(self, key: TEvent, callback: TCallable) -> None:
        if key in self._subscriptions:
            self._subscriptions[key].unsubscribe(callback)
            if not self._subscriptions[key].subscriber_count:
                del self._subscriptions[key]
        else:
            raise KeyError(f"No subscriber found for event keyed by: {self._key_name(key)}.")

    def clear_event(self, key: TEvent) -> None:
        if key in self._subscriptions:
            self._subscriptions[key].unsubscribe_all()
            del self._subscriptions[key]
        else:
            raise KeyError(f"No event found for key: {self._key_name(key)}.")

    def clear_all_events(self) -> None:
        for key in list(self._subscriptions.keys()):
            self.clear_event(key)

    @abstractmethod
    def _key_name(self, key: TEvent) -> str:
        raise NotImplementedError()
