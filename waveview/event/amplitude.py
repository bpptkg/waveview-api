from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.utils.module_loading import import_string

from waveview.inventory.datastream import DataStream


@dataclass
class SignalAmplitude:
    time: datetime
    duration: float
    amplitude: float
    method: str
    category: str
    unit: str
    stream_id: str
    channel_id: str
    preferred: bool = False


class AmplitudeCalculator:
    method: str = ""

    def __init__(self) -> None:
        self.datastream = DataStream(connection)

    def calc(
        self, time: datetime, duration: float, channel_id: str, organization_id: str
    ) -> SignalAmplitude:
        raise NotImplementedError


class AmplitudeCalculatorRegistry:
    def __init__(self):
        self._calculators: dict[str, AmplitudeCalculator] = {}

    def register(self, calculator: AmplitudeCalculator) -> None:
        if calculator.method in self._calculators:
            raise ValueError(f"Calculator {calculator.method} is already registered.")
        self._calculators[calculator.method] = calculator

    def unregister(self, method: str) -> None:
        if method in self._calculators:
            del self._calculators[method]

    def get(self, method: str) -> AmplitudeCalculator:
        if method not in self._calculators:
            raise ValueError(f"Calculator {method} is not registered.")
        return self._calculators.get(method)

    def has(self, method: str) -> bool:
        return method in self._calculators


amplitude_registry = AmplitudeCalculatorRegistry()


def register_amplitude_calculators() -> None:
    for method in settings.AMPLITUDE_CALCULATOR_REGISTRY:
        calculator = import_string(method)()
        amplitude_registry.register(calculator)
