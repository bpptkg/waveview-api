import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import numpy as np
from django.db import connection

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel
from waveview.signal.packet import Packet
from waveview.utils import timestamp

logger = logging.getLogger(__name__)


@dataclass
class FetcherData:
    request_id: str
    channel_id: str
    start: float
    end: float
    force_center: bool

    @classmethod
    def from_raw_data(cls, raw: dict) -> "FetcherData":
        return cls(
            request_id=raw["requestId"],
            channel_id=raw["channelId"],
            start=raw["start"],
            end=raw["end"],
            force_center=raw.get("forceCenter", True),
        )


class BaseStreamFetcher:
    def fetch(self, payload: FetcherData) -> bytes:
        raise NotImplementedError("fetch method must be implemented")


class DummyStreamFetcher(BaseStreamFetcher):
    def fetch(self, payload: FetcherData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        n_out = 6000

        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)
        now = datetime.now(timezone.utc)

        starttime = start
        endtime = end if end < now else now

        if starttime > now:
            x = np.array([], dtype=np.float64)
            y = np.array([], dtype=np.float64)
        else:
            x = np.linspace(
                starttime.timestamp() * 1000, endtime.timestamp() * 1000, n_out
            ).astype(np.float64)
            y = np.sin(x).astype(np.float64)
            noise = np.random.normal(0, 0.5, y.shape)
            y += noise

        packet = Packet(
            request_id=request_id,
            command="stream.fetch",
            channel_id=channel_id,
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            x=x,
            y=y,
        )
        return packet.encode()


class TimescaleStreamFetcher(BaseStreamFetcher):
    def __init__(self) -> None:
        self.datastream = DataStream(connection)

    def fetch(self, payload: FetcherData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        force_center = payload.force_center

        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)

        empty_packet = Packet(
            request_id=request_id,
            channel_id=channel_id,
            command="stream.fetch",
            start=timestamp.to_milliseconds(start),
            end=timestamp.to_milliseconds(end),
            x=np.array([]),
            y=np.array([]),
        )

        try:
            Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            logger.debug(f"Channel {channel_id} not found.")
            return empty_packet.encode()

        st = self.datastream.get_waveform(channel_id, start, end)
        st.resample(10)
        if len(st) == 0:
            return empty_packet.encode()

        if force_center:
            st.detrend("linear")

        starttime = st[0].stats.starttime
        npts = st[0].stats.npts
        delta = st[0].stats.delta
        a = np.array(
            [starttime.timestamp * 1000 + i * delta * 1000 for i in range(npts)],
            dtype=np.float64,
        )
        b = st[0].data.astype(np.float64)

        packet = Packet(
            request_id=request_id,
            channel_id=channel_id,
            command="stream.fetch",
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            x=a,
            y=b,
        )
        return packet.encode()


def get_fetcher_adapter() -> BaseStreamFetcher:
    return TimescaleStreamFetcher()
