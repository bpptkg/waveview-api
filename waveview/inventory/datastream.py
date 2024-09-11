import logging
import zlib
from datetime import datetime
from uuid import UUID

import numpy as np
import psycopg2
import zstandard as zstd
from django.utils import timezone
from obspy import Stream, Trace, UTCDateTime
from obspy.core import Stats

from waveview.inventory.db.schema import TimescaleSchemaEditor
from waveview.inventory.models import Channel

logger = logging.getLogger(__name__)

UUIDType = UUID | str


def preparebuffer(trace: Trace) -> tuple[datetime, datetime, float, str, bytes]:
    starttime: UTCDateTime = trace.stats.starttime
    endtime: UTCDateTime = trace.stats.endtime
    sample_rate = trace.stats.sampling_rate
    dtype = str(trace.data.dtype)
    st = starttime.datetime.replace(tzinfo=timezone.utc)
    et = endtime.datetime.replace(tzinfo=timezone.utc)
    compressor = zstd.ZstdCompressor()
    buf = compressor.compress(trace.data.tobytes())
    return st, et, sample_rate, dtype, buf


def mergebuffer(rows: tuple[datetime, datetime, float, str, bytes]) -> np.ndarray:
    if len(rows) == 0:
        return np.array([])
    decompressor = zstd.ZstdDecompressor()
    return np.frombuffer(
        b"".join([decompressor.decompress(row[4]) for row in rows]), dtype=rows[0][3]
    )


class DataStream:
    """
    DataStream class is a wrapper around the TimescaleSchemaEditor class to
    provide an interface to query and insert data into the database.
    """

    def __init__(self, connection: psycopg2.extensions.connection) -> None:
        self.db = TimescaleSchemaEditor(connection)

    def get_waveform(
        self, channel_id: UUIDType | list[UUIDType], start: datetime, end: datetime
    ) -> Stream:
        if isinstance(channel_id, list):
            traces = self.get_multi_trace(channel_id, start, end)
        else:
            traces = self.get_trace(channel_id, start, end)
        return Stream(traces=traces)

    def get_multi_trace(
        self, channel_ids: list[UUIDType], start: datetime, end: datetime
    ) -> Trace:
        traces = []
        for channel_id in channel_ids:
            trace = self.get_trace(channel_id, start, end)
            traces.append(trace)
        return traces

    def get_trace(self, channel_id: UUIDType, start: datetime, end: datetime) -> Trace:
        try:
            channel = Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            raise ValueError(f"Channel {channel_id} does not exist")

        sample_rate = channel.sample_rate
        if sample_rate is None:
            raise ValueError(f"Channel {channel_id} does not have a sample rate")

        table = channel.get_datastream_id()
        rows = self.db.query(table, start, end)
        data = mergebuffer(rows)
        if len(rows) > 0:
            starttime = UTCDateTime(rows[0][0])
        else:
            starttime = UTCDateTime(start)

        stats = Stats()
        stats.network = channel.station.network.code
        stats.station = channel.station.code
        stats.location = channel.location_code
        stats.channel = channel.code
        stats.starttime = starttime
        stats.sampling_rate = sample_rate
        stats.npts = len(data)

        trace = Trace(data=data, header=stats)
        return trace

    def insert_stream(self, stream: Stream) -> None:
        for trace in stream:
            self.insert_trace(trace)

    def insert_trace(self, trace: Trace) -> None:
        network = trace.stats.network
        station = trace.stats.station
        channel = trace.stats.channel
        sample_rate = trace.stats.sampling_rate
        dtype = str(trace.data.dtype)
        buf = zlib.compress(trace.data.tobytes())
        obj = Channel.objects.filter(
            code=channel, station__code=station, station__network__code=network
        ).first()
        if not obj:
            logger.error(f"Channel {network}.{station}.{channel} not found.")
            return
        table = obj.get_datastream_id()
        st, et, sample_rate, dtype, buf = preparebuffer(trace)
        self.db.insert(table, st, et, sample_rate, dtype, buf)
