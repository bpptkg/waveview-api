from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

from waveview.appconfig.models import MagnitudeConfig


@dataclass
class MagnitudeCalculatorData:
    organization_id: str
    volcano_id: str
    event_id: str
    author_id: str


class BaseMagnitudeCalculator(ABC):
    method: str

    def __init__(self, config: MagnitudeConfig) -> None:
        super().__init__()

        self.config = config

    @abstractmethod
    def calc_magnitude(self, data: MagnitudeCalculatorData) -> None:
        pass


class MagnitudeCalculatorRegistry:
    def __init__(self) -> None:
        self._calculators: dict[str, Type[BaseMagnitudeCalculator]] = {}

    def register(self, method: str, klass: Type[BaseMagnitudeCalculator]):
        self._calculators[method] = klass

    def get(self, method: str) -> Type[BaseMagnitudeCalculator] | None:
        return self._calculators.get(method)

    def get_all(self) -> dict[str, Type[BaseMagnitudeCalculator]]:
        return self._calculators


registry = MagnitudeCalculatorRegistry()


def register_magnitude_calculator(
    method: str, klass: Type[BaseMagnitudeCalculator]
) -> None:
    registry.register(method, klass)


def get_magnitude_calculator(method: str) -> Type[BaseMagnitudeCalculator]:
    return registry.get(method)
