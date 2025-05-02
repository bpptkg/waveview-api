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
class FetcherRequestData:
    request_id: str
    channel_id: str
    start: float
    end: float
    force_center: bool
    resample: bool
    sample_rate: int

    @classmethod
    def from_raw_data(cls, raw: dict) -> "FetcherRequestData":
        start = raw["start"]
        end = raw["end"]
        return cls(
            request_id=raw["requestId"],
            channel_id=raw["channelId"],
            start=int(start),
            end=int(end),
            force_center=raw.get("forceCenter", True),
            resample=raw.get("resample", True),
            sample_rate=raw.get("sampleRate", 1),
        )


class BaseStreamFetcher:
    def fetch(self, payload: FetcherRequestData) -> bytes:
        raise NotImplementedError("fetch method must be implemented")


class TimescaleStreamFetcher(BaseStreamFetcher):
    def __init__(self) -> None:
        self.datastream = DataStream(connection)

    def fetch(self, payload: FetcherRequestData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        force_center = payload.force_center
        sample_rate = payload.sample_rate
        resample = payload.resample

        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)

        encoder = StreamEncoder()

        empty = encoder.encode_stream(
            StreamData(
                request_id=request_id,
                channel_id=channel_id,
                command="stream.fetch",
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

        if force_center:
            st.detrend("demean")

        st.merge(method=0, fill_value=None)
        st = st.split()

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


def get_fetcher_adapter() -> BaseStreamFetcher:
    return TimescaleStreamFetcher()
