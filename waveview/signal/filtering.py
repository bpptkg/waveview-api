import enum
import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BandpassFilterParam:
    freqmin: float
    freqmax: float
    order: int
    zerophase: bool


@dataclass
class LowpassFilterParam:
    freq: float
    order: int
    zerophase: bool


@dataclass
class HighpassFilterParam:
    freq: float
    order: int
    zerophase: bool


class FilterType(enum.StrEnum):
    BANDPASS = "bandpass"
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"


@dataclass
class FilterData:
    request_id: str
    channel_id: str
    start: float
    end: float
    filter_type: str
    filter_params: dict


class BaseFilterAdapter:
    def filter(self, payload: FilterData) -> bytes:
        raise NotImplementedError("filter method must be implemented")


class DummyFilterAdapter(BaseFilterAdapter):
    def filter(self, payload: FilterData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        n_out = 6000

        return np.random.rand(n_out).tobytes()
