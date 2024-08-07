from datetime import datetime

import numpy as np
import psycopg2
from obspy import Stream, Trace, UTCDateTime
from obspy.core import Stats

from waveview.inventory.models import Channel
from waveview.signal.stream_id import StreamIdentifier


class StreamIO:
    def __init__(self, connection: psycopg2.extensions.connection) -> None:
        self.connection = connection

    def to_trace(self, rows: list[tuple[datetime, float]], stream_id: str) -> Trace:
        data = np.array([row[1] for row in rows])
        sid = StreamIdentifier(id=stream_id)
        channel = Channel.objects.filter(
            code=sid.channel,
            station__code=sid.station,
            station__network__code=sid.network,
        ).first()
        if not channel:
            raise ValueError(
                f"Channel {sid.network}.{sid.station}.{sid.location}.{sid.channel} not found."
            )

        sample_rate = channel.sample_rate
        if sample_rate is None:
            sample_rate = rows[1][0] - rows[0][0]

        stats = Stats()
        stats.network = sid.network
        stats.station = sid.station
        stats.location = sid.location
        stats.channel = sid.channel
        stats.starttime = UTCDateTime(rows[0][0])
        stats.sampling_rate = sample_rate
        stats.npts = len(data)

        trace = Trace(data=data, header=stats)
        return trace

    def to_stream(self, rows: list[tuple[datetime, float]], stream_id: str) -> Stream:
        trace = self.to_trace(rows, stream_id)
        return Stream(traces=[trace])
