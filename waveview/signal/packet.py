import datetime

import lttbc
import numpy as np
from obspy import UTCDateTime, read


class Packet:
    def __init__(self, x: np.ndarray, y: np.ndarray, start: float, end: float) -> None:
        self.x = x
        self.y = y
        self.start = start
        self.end = end

    def encode(self) -> bytes:
        y = self.y.copy()
        x = self.x.copy()
        n_out = min(len(y), 100 * 60)
        a, b = lttbc.downsample(x, y, n_out)
        header = np.array(
            [
                len(a),
                self.start,
                self.end,
                0,
                0,
                0,
                0,
                0,
            ],
            dtype=np.int64,
        )
        return header.tobytes() + a.tobytes() + b.tobytes()


path = "/Users/iori/Projects/testonly/MEPAS.msd"
st = read(path)


def get_data(start: float, end: float) -> bytes:
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

    x = np.linspace(start, end, len(trace.data))
    y = trace.data

    packet = Packet(x, y, start, end)
    return packet.encode()
