import enum
from typing import Type

from django.conf import settings
from django.utils.module_loading import import_string


class OperationType(enum.StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class EventObserver:
    name: str = ""

    def create(self, event_id: str, data: dict) -> None:
        pass

    def update(self, event_id: str, data: dict) -> None:
        pass

    def delete(self, event_id: str, data: dict) -> None:
        pass


class EventObserverRegistry:
    def __init__(self):
        self._observers: dict[str, Type[EventObserver]] = {}

    def register(self, observer_class: Type[EventObserver]) -> None:
        name = observer_class.name
        if name in self._observers:
            raise ValueError(f"Observer {name} is already registered.")
        self._observers[name] = observer_class

    def unregister(self, name: str) -> None:
        if name in self._observers:
            del self._observers[name]

    def get(self, name: str) -> Type[EventObserver]:
        if name not in self._observers:
            raise ValueError(f"Observer {name} is not registered.")
        return self._observers.get(name)

    def has(self, name: str) -> bool:
        return name in self._observers


observer_registry = EventObserverRegistry()


def register_observers() -> None:
    for name in settings.EVENT_OBSERVER_REGISTRY:
        name: str
        observer_class: Type[EventObserver] = import_string(name)
        observer_registry.register(observer_class)
