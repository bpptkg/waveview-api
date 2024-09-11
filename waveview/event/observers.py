from typing import Type

from django.conf import settings
from django.utils.module_loading import import_string

from waveview.event.models import Event


class EventObserver:
    def run(self, event: Event) -> None:
        """
        Run the observer for the given event.

        This method should ideally be used with an asynchronous approach to
        avoid blocking the main thread. Running this method synchronously may
        lead to performance issues, especially if the observer performs
        time-consuming operations.
        """
        pass


class EventRegistry:
    def __init__(self):
        self._observers: list[EventObserver] = []

    def register(self, observer: EventObserver) -> None:
        self._observers.append(observer)

    def notify(self, event: Event) -> None:
        for observer in self._observers:
            observer.run(event)


event_registry = EventRegistry()
for path in settings.EVENT_OBSERVERS:
    path: str
    observer: Type[EventObserver] = import_string(path)
    event_registry.register(observer())
