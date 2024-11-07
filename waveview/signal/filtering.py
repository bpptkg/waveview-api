import enum
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from django.db import connection

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel
from waveview.signal.packet import Packet
from waveview.utils import timestamp

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

        empty_packet = Packet(
            request_id=request_id,
            channel_id=channel_id,
            command="stream.filter",
            start=timestamp.to_milliseconds(start),
            end=timestamp.to_milliseconds(end),
            time=0,
            sample_rate=1,
            x=np.array([]),
            y=np.array([]),
        )

        try:
            Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            logger.debug(f"Channel {channel_id} not found.")
            return empty_packet.encode()

        st = self.datastream.get_waveform(channel_id, start, end)
        if len(st) == 0 or st[0].stats.npts == 0:
            return empty_packet.encode()

        st.detrend("demean")

        if payload.taper_type != "none":
            st.taper(max_percentage=payload.taper_width, type=payload.taper_type)

        if payload.filter_type == FilterType.BANDPASS:
            filter_param = BandpassFilterParam(**payload.filter_options)
            st.filter(
                "bandpass",
                freqmin=filter_param.freqmin,
                freqmax=filter_param.freqmax,
                corners=filter_param.order,
                zerophase=filter_param.zerophase,
            )
        elif payload.filter_type == FilterType.LOWPASS:
            filter_param = LowpassFilterParam(**payload.filter_options)
            st.filter(
                "lowpass",
                freq=filter_param.freq,
                corners=filter_param.order,
                zerophase=filter_param.zerophase,
            )
        elif payload.filter_type == FilterType.HIGHPASS:
            filter_param = HighpassFilterParam(**payload.filter_options)
            st.filter(
                "highpass",
                freq=filter_param.freq,
                corners=filter_param.order,
                zerophase=filter_param.zerophase,
            )
        else:
            return empty_packet.encode()

        if resample:
            st.resample(sample_rate)

        starttime = st[0].stats.starttime
        npts = st[0].stats.npts
        delta = st[0].stats.delta
        a = np.array(
            [starttime.timestamp * 1000 + i * delta * 1000 for i in range(npts)],
            dtype=np.float64,
        )
        b = st[0].data.astype(np.float64)

        # start and end time of the packet need to be the same as the original
        # request as the client uses these values to cache the data. If the data
        # is resampled, the start and end time of the packet will be different
        # from the original request. But it should not affect the caching
        # mechanism as the point will be plotted at the same time.
        packet = Packet(
            request_id=request_id,
            channel_id=channel_id,
            command="stream.filter",
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            time=starttime.timestamp * 1000,
            sample_rate=1 / delta,
            x=a,
            y=b,
        )
        return packet.encode()


def get_filter_adapter() -> BaseFilterAdapter:
    return TimescaleFilterAdapter()
