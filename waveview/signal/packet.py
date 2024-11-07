import logging
from dataclasses import dataclass

import numpy as np
import zstandard as zstd

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
        data = b"".join(
            [
                request_id,
                command,
                channel_id,
                header.tobytes(),
                self.x.tobytes(),
                self.y.tobytes(),
            ]
        )
        compressor = zstd.ZstdCompressor()
        compressed = compressor.compress(data)
        return compressed

    @classmethod
    def decode(cls: "Packet", data: bytes) -> "Packet":
        raise NotImplementedError("decode method must be implemented")
