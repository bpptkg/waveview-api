import enum
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from django.db import connection

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel
from waveview.signal.encoder import StreamData, StreamEncoder
from waveview.utils import timestamp

logger = logging.getLogger(__name__)


@dataclass
class BandpassFilterParam:
    freqmin: float
    freqmax: float
    order: int
    zerophase: bool

    @classmethod
    def from_dict(cls, data: dict) -> "BandpassFilterParam":
        freqmin = data["freqmin"]
        if freqmin <= 0:
            freqmin = 0.01
        freqmax = data["freqmax"]
        order = data["order"]
        zerophase = data["zerophase"]
        return cls(
            freqmin=freqmin,
            freqmax=freqmax,
            order=order,
            zerophase=zerophase,
        )


@dataclass
class LowpassFilterParam:
    freq: float
    order: int
    zerophase: bool

    @classmethod
    def from_dict(cls, data: dict) -> "LowpassFilterParam":
        freq = data["freq"]
        if freq <= 0:
            freq = 0.01
        order = data["order"]
        zerophase = data["zerophase"]
        return cls(
            freq=freq,
            order=order,
            zerophase=zerophase,
        )


@dataclass
class HighpassFilterParam:
    freq: float
    order: int
    zerophase: bool

    @classmethod
    def from_dict(cls, data: dict) -> "HighpassFilterParam":
        freq = data["freq"]
        if freq <= 0:
            freq = 0.01
        order = data["order"]
        zerophase = data["zerophase"]
        return cls(
            freq=freq,
            order=order,
            zerophase=zerophase,
        )


class FilterType(enum.StrEnum):
    BANDPASS = "bandpass"
    LOWPASS = "lowpass"
    HIGHPASS = "highpass"


@dataclass
class FilterRequestData:
    request_id: str
    channel_id: str
    start: float
    end: float
    filter_type: str
    filter_options: dict
    taper_type: str
    taper_width: float
    resample: bool
    sample_rate: int

    @classmethod
    def from_raw_data(cls, data: dict) -> "FilterRequestData":
        start = data["start"]
        end = data["end"]
        return cls(
            request_id=data["requestId"],
            channel_id=data["channelId"],
            start=int(start),
            end=int(end),
            filter_type=data["filterType"],
            filter_options=data["filterOptions"],
            taper_type=data["taperType"],
            taper_width=data["taperWidth"],
            resample=data.get("resample", True),
            sample_rate=data.get("sampleRate", 10),
        )


class BaseFilterAdapter:
    def filter(self, payload: FilterRequestData) -> bytes:
        raise NotImplementedError("filter method must be implemented")


class TimescaleFilterAdapter(BaseFilterAdapter):
    def __init__(self) -> None:
        self.datastream = DataStream(connection)

    def filter(self, payload: FilterRequestData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)
        resample = payload.resample
        sample_rate = payload.sample_rate

        encoder = StreamEncoder()
        empty = encoder.encode_stream(
            StreamData(
                request_id=request_id,
                channel_id=channel_id,
                command="stream.filter",
                start=timestamp.to_milliseconds(start),
                end=timestamp.to_milliseconds(end),
                trace=None,
            )
        )

        try:
            Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            logger.debug(f"Channel {channel_id} not found.")
            return empty

        st = self.datastream.get_waveform(channel_id, start, end)
        if len(st) == 0:
            return empty

        st.detrend("demean")

        if payload.taper_type != "none":
            st.taper(max_percentage=payload.taper_width, type=payload.taper_type)

        try:
            if payload.filter_type == FilterType.BANDPASS:
                filter_param = BandpassFilterParam.from_dict(payload.filter_options)
                st.filter(
                    "bandpass",
                    freqmin=filter_param.freqmin,
                    freqmax=filter_param.freqmax,
                    corners=filter_param.order,
                    zerophase=filter_param.zerophase,
                )
            elif payload.filter_type == FilterType.LOWPASS:
                filter_param = LowpassFilterParam.from_dict(payload.filter_options)
                st.filter(
                    "lowpass",
                    freq=filter_param.freq,
                    corners=filter_param.order,
                    zerophase=filter_param.zerophase,
                )
            elif payload.filter_type == FilterType.HIGHPASS:
                filter_param = HighpassFilterParam.from_dict(payload.filter_options)
                st.filter(
                    "highpass",
                    freq=filter_param.freq,
                    corners=filter_param.order,
                    zerophase=filter_param.zerophase,
                )
            else:
                return empty
        except Exception as e:
            logger.error(f"Error filtering data: {e}")
            return empty

        if resample:
            st.resample(sample_rate)

        st.merge(method=0, fill_value=None)
        trace = st[0]
        if len(trace.data) == 0:
            return empty

        return encoder.encode_stream(
            StreamData(
                request_id=request_id,
                channel_id=channel_id,
                command="stream.fetch",
                start=timestamp.to_milliseconds(start),
                end=timestamp.to_milliseconds(end),
                trace=trace,
            )
        )


def get_filter_adapter() -> BaseFilterAdapter:
    return TimescaleFilterAdapter()
