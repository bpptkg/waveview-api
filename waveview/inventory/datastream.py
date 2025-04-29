import logging
from datetime import datetime, timedelta
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
    st.merge(method=0, fill_value=0)
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
        """
        Get waveform data for a given channel and time range.

        Parameters
        ----------
        channel_id : UUIDType
            Channel ID.
        start : datetime
            Start time of the waveform data to retrieve in UTC.
        end : datetime
            End time of the waveform data to retrieve in UTC.

        Returns
        -------
        Stream
            ObsPy Stream object containing waveform data.
        """

        try:
            channel = Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            raise ValueError(f"Channel {channel_id} does not exist")

        # Add buffer in seconds to start and end time to ensure we get all the
        # chunks of data within the range.
        buffer = timedelta(seconds=8)
        table = channel.get_datastream_id()
        rows = self.db.query(table, start - buffer, end + buffer)
        st = build_traces(rows, channel)
        st.trim(starttime=UTCDateTime(start), endtime=UTCDateTime(end))
        return st

    def load_stream(
        self,
        stream: Stream,
        chunksize: float = 2,
        table: str = None,
        print_stats: bool = False,
    ) -> None:
        """
        Load a stream of data into the database.

        Parameters
        ----------
        stream : Stream
            ObsPy Stream object containing traces to be loaded.
        chunksize : float, optional
            Chunk size in seconds. Default is 2 seconds.
        table : str, optional
            Table name to insert data into. If not provided, the table name
            will be fetched from the channel object. Default is None.
        print_stats : bool, optional
            Print data load statistics. Default is False.
        """
        nbytes: int = 0
        compressed: int = 0

        for trace in stream:
            trace: Trace
            stream_id = trace.id
            if table is None:
                try:
                    channel = Channel.objects.get_by_stream_id(stream_id)
                except Channel.DoesNotExist:
                    logger.warning(f"Channel {stream_id} not found. Skipping.")
                    continue
                table = channel.get_datastream_id()

            starttime = trace.stats.starttime
            endtime = trace.stats.endtime

            while starttime < endtime:
                chunk_start = starttime
                chunk_end = starttime + chunksize
                if chunk_end > endtime:
                    chunk_end = endtime

                chunk = trace.slice(chunk_start, chunk_end)
                st, et, sr, dtype, buf = prepare_buffer(chunk)
                self.db.insert(table, st, et, sr, dtype, buf)

                nbytes += chunk.data.nbytes
                compressed += len(buf)

                starttime = chunk_end

        if print_stats:
            logger.info(
                f"Data loaded: {nbytes:,} bytes, compressed: {compressed:,} bytes."
            )
            compression_ratio = (compressed / nbytes) * 100
            logger.info(f"Compression ratio: {compression_ratio:.2f}%")
