import logging
from dataclasses import dataclass
from datetime import datetime

from django.db import connection
from obspy import Stream

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel

logger = logging.getLogger(__name__)


@dataclass
class ResolvedWaveform:
    stream: Stream
    channel: Channel | None = None
    resolved: bool = True


class WaveformResolver:
    def __init__(self) -> None:
        self.db = DataStream(connection)

    def get_waveform(self, start: datetime, end: datetime) -> ResolvedWaveform:
        stream_ids = (
            "VG.MEPAS.00.HHZ",
            "VG.MEPSL.00.HHZ",
            "VG.MELAB.00.HHZ",
        )

        for stream_id in stream_ids:
            try:
                channel = Channel.objects.get_by_stream_id(stream_id)
                st = self.db.get_waveform(channel, start, end)
                st.merge(fill_value="interpolate")
                if len(st) > 0:
                    return ResolvedWaveform(stream=st, channel=channel)
            except Exception as e:
                logger.debug(f"Failed to get waveform for stream ID {stream_id}: {e}")
        return ResolvedWaveform(stream=Stream(), channel=None, resolved=False)
