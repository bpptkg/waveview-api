import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import numpy as np
from django.db import connection

from waveview.inventory.db.query import TimescaleQuery
from waveview.inventory.models import Channel
from waveview.utils import timestamp

logger = logging.getLogger(__name__)


def pad(a: bytes, n: int) -> bytes:
    if len(a) >= n:
        return a[:n]
    return a.ljust(n, b"\0")


@dataclass(frozen=True)
class Packet:
    x: np.ndarray
    y: np.ndarray
    start: int
    end: int
    channel_id: str

    def encode(self) -> bytes:
        channel_id = pad(self.channel_id.encode("utf-8"), 64)
        header = np.array(
            [
                int(self.start),
                int(self.end),
                len(self.x),
                len(self.y),
                0,
                0,
                0,
                0,
            ],
            dtype=np.uint64,
        )
        return b"".join(
            [
                channel_id,
                header.tobytes(),
                self.x.tobytes(),
                self.y.tobytes(),
            ]
        )

    @classmethod
    def decode(cls: "Packet", data: bytes) -> "Packet":
        channel_id = data[:64].decode("utf-8").strip("\0")
        header = np.frombuffer(data[64 : 64 + 8 * 8], dtype=np.uint64)
        start = int(header[0])
        end = int(header[1])
        x = np.frombuffer(
            data[64 + 8 * 8 : 64 + 8 * 8 + 8 * header[2]], dtype=np.float64
        )
        y = np.frombuffer(data[64 + 8 * 8 + 8 * header[2] :], dtype=np.float64)
        return cls(x=x, y=y, start=start, end=end, channel_id=channel_id)


@dataclass
class FetcherData:
    channel_id: str
    start: float
    end: float
    mode: Literal[
        "match_width",
        "max_points",
        "none",
        "auto",
    ]
    width: float
    max_points: int

    @classmethod
    def parse_raw(cls, raw: dict) -> "FetcherData":
        return cls(
            channel_id=raw["channelId"],
            start=raw["start"],
            end=raw["end"],
            mode=raw["mode"],
            width=raw.get("width", 0),
            max_points=raw.get("max_points", 0),
        )


class StreamFetcher:
    def __init__(self) -> None:
        self.query = TimescaleQuery(connection=connection)

    def fetch(self, payload: FetcherData) -> bytes:
        channel_id = payload.channel_id
        width = payload.width
        mode = payload.mode
        max_points = payload.max_points

        if mode == "auto":
            n_out = int(width * 2)
        elif mode == "match_width":
            n_out = int(width)
        elif mode == "max_points":
            n_out = max_points
        else:
            n_out = -1

        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)

        empty_packet = Packet(
            channel_id=channel_id,
            start=timestamp.to_milliseconds(start),
            end=timestamp.to_milliseconds(end),
            x=np.array([]),
            y=np.array([]),
        )

        try:
            channel = Channel.objects.get(channel_id=channel_id)
        except Channel.DoesNotExist:
            logger.debug(f"Channel {channel_id} not found.")
            return empty_packet.encode()

        table = channel.get_datastream_id()

        if n_out == -1:
            data = self.query.fetch(
                start=start,
                end=end,
                table=table,
            )
        else:
            data = self.query.fetch_lttb(
                start=start,
                end=end,
                table=table,
                max_points=n_out,
            )

        a = np.array([x[0] for x in data])
        b = np.array([x[1] for x in data])

        packet = Packet(
            channel_id=channel_id,
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            x=a,
            y=b,
        )
        return packet.encode()
