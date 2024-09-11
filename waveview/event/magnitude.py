from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

from waveview.appconfig.models import MagnitudeConfig


@dataclass
class MagnitudeEstimatorData:
    organization_id: str
    volcano_id: str
    event_id: str
    author_id: str


class BaseMagnitudeEstimator(ABC):
    method: str

    def __init__(self, config: MagnitudeConfig) -> None:
        super().__init__()

        self.config = config

    @abstractmethod
    def calc_magnitude(self, data: MagnitudeEstimatorData) -> None:
        pass


class MagnitudeEstimatorRegistry:
    def __init__(self) -> None:
        self._calculators: dict[str, Type[BaseMagnitudeEstimator]] = {}

    def register(self, method: str, klass: Type[BaseMagnitudeEstimator]):
        self._calculators[method] = klass

    def get(self, method: str) -> Type[BaseMagnitudeEstimator] | None:
        return self._calculators.get(method)

    def all(self) -> dict[str, Type[BaseMagnitudeEstimator]]:
        return self._calculators


registry = MagnitudeEstimatorRegistry()


def register_magnitude_estimator(
    method: str, klass: Type[BaseMagnitudeEstimator]
) -> None:
    registry.register(method, klass)


def get_magnitude_estimator(method: str) -> Type[BaseMagnitudeEstimator]:
    return registry.get(method)
