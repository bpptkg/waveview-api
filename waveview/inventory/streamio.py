from datetime import datetime
from uuid import UUID

import numpy as np
import psycopg2
from obspy import Stream, Trace, UTCDateTime
from obspy.core import Stats

from waveview.inventory.db.query import TimescaleQuery
from waveview.inventory.models import Channel

UUIDType = UUID | str


class DataStream:
    def __init__(self, connection: psycopg2.extensions.connection) -> None:
        self.query = TimescaleQuery(connection)

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
        rows = self.query.fetch(start, end, table)
        data = np.array([row[1] for row in rows])
        if len(data) == 0:
            starttime = UTCDateTime(start)
        else:
            starttime = UTCDateTime(rows[0][0])

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
