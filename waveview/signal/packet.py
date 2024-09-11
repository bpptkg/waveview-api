import logging
from dataclasses import dataclass

import numpy as np
import uuid

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
    request_id: str
    command: str

    def encode(self) -> bytes:
        request_id = pad(self.request_id.encode("utf-8"), 64)
        command = pad(self.command.encode("utf-8"), 64)
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
                request_id,
                command,
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
