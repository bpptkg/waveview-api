import datetime
from dataclasses import dataclass
from typing import Literal

import numpy as np
from obspy import Trace, UTCDateTime, read


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


path = "/Users/iori/Projects/testonly/MEPAS.msd"
st = read(path)


def get_data(start: float, end: float) -> Trace:
    """
    Stream1: 1 Trace(s) in Stream:
    VG.MEPAS.00.HHZ | 2024-06-10T08:00:00.000000Z - 2024-06-12T08:00:00.000000Z | 100.0 Hz, 17280001 samples
    """
    starttime = UTCDateTime(start / 1000).replace(year=2024, month=6, day=11)
    endtime = UTCDateTime(end / 1000).replace(year=2024, month=6, day=11)
    if starttime > endtime:
        starttime = starttime - datetime.timedelta(days=1)

    ns = st.slice(starttime=starttime, endtime=endtime)
    trace = ns[0]

    return trace


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
    def __init__(self, payload: FetcherData) -> None:
        self.payload = payload

    def fetch(self) -> bytes:
        channel_id = self.payload.channel_id
        start = self.payload.start
        end = self.payload.end
        width = self.payload.width
        mode = self.payload.mode

        trace = get_data(start, end)
        x = np.linspace(start, end, num=len(trace.data))
        y = trace.data

        if mode == "auto":
            n_out = int(width * 2)
        elif mode == "match_width":
            n_out = int(width)
        elif mode == "max_points":
            max_points = self.payload.max_points
            n_out = np.min([len(y), max_points])
        else:
            n_out = len(y)

        a, b = lttbc.downsample(x, y, n_out)
        packet = Packet(
            channel_id=channel_id,
            start=start,
            end=end,
            x=a,
            y=b,
        )
        return packet.encode()
