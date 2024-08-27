import random
from datetime import datetime
from typing import Any

from django.utils import timezone

from waveview.event.header import EvaluationMode, EvaluationStatus


def random_datetime(days: int = 365) -> datetime:
    return timezone.now() - timezone.timedelta(days=random.randint(0, days))


def random_duration() -> float:
    return random.uniform(10.0, 200.0)


def random_choices(choices: list[Any]) -> Any:
    return random.choice(choices)


def random_methods() -> str:
    choices = [
        "WaveView",
        "HypoDD",
        "NonLinLoc",
        "HypoInverse",
        "Hypo71",
    ]
    return random_choices(choices)


def random_evaluation_mode() -> str:
    choices = [
        EvaluationMode.AUTOMATIC,
        EvaluationMode.MANUAL,
    ]
    return random_choices(choices)


def random_evaluation_status() -> str:
    choices = [
        EvaluationStatus.PRELIMINARY,
        EvaluationStatus.CONFIRMED,
    ]
    return random_choices(choices)


def random_range(left: float, right: float) -> float:
    return random.uniform(left, right)
