from abc import ABC, abstractmethod


class BaseMagnitudeCalculator(ABC):
    method: str

    @abstractmethod
    def calc_magnitude(
        self, organization_id: str, volcano_id: str, event_id: str
    ) -> None:
        pass


class MagnitudeCalculatorRegistry:
    def __init__(self) -> None:
        self._calculators: dict[str, BaseMagnitudeCalculator] = {}

    def register(self, method: str, calculator: BaseMagnitudeCalculator):
        self._calculators[method] = calculator

    def get(self, method: str) -> BaseMagnitudeCalculator:
        return self._calculators[method]

    def get_all(self) -> dict[str, BaseMagnitudeCalculator]:
        return self._calculators


registry = MagnitudeCalculatorRegistry()


def register_magnitude_calculator(
    method: str, calculator: BaseMagnitudeCalculator
) -> None:
    registry.register(method, calculator)


def get_magnitude_calculator(method: str) -> BaseMagnitudeCalculator:
    return registry.get(method)
