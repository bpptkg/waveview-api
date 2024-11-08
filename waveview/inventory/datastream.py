import io
import logging
import zlib
from datetime import datetime, timedelta
from uuid import UUID

import numpy as np
import psycopg2
import zstandard as zstd
from django.utils import timezone
from obspy import Stream, Trace, UTCDateTime, read
from obspy.core import Stats

from waveview.inventory.db.schema import TimescaleSchemaEditor
from waveview.inventory.models import Channel

logger = logging.getLogger(__name__)

UUIDType = UUID | str
BufferType = tuple[datetime, datetime, float, str, bytes]


def prepare_buffer(trace: Trace) -> BufferType:
    """
    Prepare trace data for insertion into the database.
    """
    starttime: UTCDateTime = trace.stats.starttime
    endtime: UTCDateTime = trace.stats.endtime
    sample_rate = trace.stats.sampling_rate
    dtype = str(trace.data.dtype)
    st = starttime.datetime.replace(tzinfo=timezone.utc)
    et = endtime.datetime.replace(tzinfo=timezone.utc)
    compressor = zstd.ZstdCompressor()
    buf = compressor.compress(trace.data.tobytes())
    return st, et, sample_rate, dtype, buf


def merge_buffer(rows: list[BufferType]) -> np.ndarray:
    """
    Merge buffer data into a single numpy array.
    """
    decompressor = zstd.ZstdDecompressor()
    return np.frombuffer(
        b"".join([decompressor.decompress(row[4]) for row in rows]), dtype=rows[0][3]
    )


def build_trace(
    row: BufferType, network: str, station: str, location: str, channel: str
) -> Trace:
    """
    Build an ObsPy Trace object from a row of buffer data.
    """
    st, et, sr, dtype, buf = row
    decompressor = zstd.ZstdDecompressor()
    data = np.frombuffer(decompressor.decompress(buf), dtype=dtype)
    starttime = UTCDateTime(st)

    stats = Stats()
    stats.network = network
    stats.station = station
    stats.location = location
    stats.channel = channel
    stats.starttime = starttime
    stats.sampling_rate = sr
    stats.npts = len(data)

    trace = Trace(data=data, header=stats)
    return trace


def build_traces(rows: BufferType, channel: Channel) -> Stream:
    """
    Build an ObsPy Stream object from a list of buffer data.
    """
    if len(rows) == 0:
        return Stream()
    traces = [
        build_trace(
            row=row,
            network=channel.station.network.code,
            station=channel.station.code,
            location=channel.location_code,
            channel=channel.code,
        )
        for row in rows
    ]
    st = Stream(traces=traces)
    st.merge(method=1, fill_value=0)
    return st


class DataStream:
    """
    DataStream class is a wrapper around the TimescaleSchemaEditor class to
    provide an interface to query and insert data into the database.
    """

    def __init__(self, connection: psycopg2.extensions.connection) -> None:
        self.db = TimescaleSchemaEditor(connection)

    def get_waveform(
        self, channel_id: UUIDType, start: datetime, end: datetime
    ) -> Stream:
        try:
            channel = Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            raise ValueError(f"Channel {channel_id} does not exist")

        table = channel.get_datastream_id()
        # Add buffer in seconds to start and end time to ensure we get all the
        # chunks of data within the range.
        buffer = 8
        rows = self.db.query(
            table, start - timedelta(seconds=buffer), end + timedelta(seconds=buffer)
        )
        st = build_traces(rows, channel)
        st.trim(starttime=UTCDateTime(start), endtime=(UTCDateTime(end)))
        return st

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
        st, et, sample_rate, dtype, buf = prepare_buffer(trace)
        self.db.insert(table, st, et, sample_rate, dtype, buf)

    def load_stream(
        self, table: str, path: str, reclen: int = 512, chunksize: int = 1
    ) -> None:
        size = reclen * chunksize

        nbytes = 0
        compressed = 0
        with io.open(path, "rb") as f:
            while True:
                with io.BytesIO() as chunk:
                    c = f.read(size)
                    if not c:
                        break
                    chunk.write(c)
                    chunk.seek(0, 0)
                    stream = read(chunk)

                for trace in stream:
                    trace: Trace
                    st, et, sr, dtype, buf = prepare_buffer(trace)
                    self.db.insert(table, st, et, sr, dtype, buf)

                    nbytes += trace.data.nbytes
                    compressed += len(buf)
