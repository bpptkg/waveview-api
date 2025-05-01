import io
import struct
from dataclasses import dataclass

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import zstandard as zstd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from obspy import Trace

matplotlib.use("Agg")


def pad(a: bytes, n: int) -> bytes:
    if len(a) >= n:
        return a[:n]
    return a.ljust(n, b"\0")


@dataclass(frozen=True)
class StreamData:
    request_id: str
    channel_id: str
    command: str
    start: int
    end: int
    trace: Trace | None


@dataclass
class SpectrogramData:
    request_id: str
    channel_id: str
    npoints: int
    sample_rate: float
    data: np.ndarray
    time: np.ndarray
    freq: np.ndarray
    start: int
    end: int
    norm: Normalize
    width: int
    height: int
    command: str = "stream.spectrogram"


def get_cmap() -> LinearSegmentedColormap:
    colors = [
        (1, 1, 1, 0),  # White
        (0, 0, 1, 1),  # Blue
        (0, 1, 0, 1),  # Green
        (1, 1, 0, 1),  # Yellow
        (1, 0, 0, 1),  # Red
    ]
    n_bins = 100
    cmap_name = "waveview"
    cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)
    return cmap


def generate_image(
    specgram: np.ndarray,
    time: np.ndarray,
    freq: np.ndarray,
    norm: Normalize,
    tmin: float,
    tmax: float,
) -> bytes:
    """
    Generate a spectrogram image from the given data.

    Parameters
    ----------
    specgram : np.ndarray
        The spectrogram data.
    time : np.ndarray
        The offset time of the spectrogram, e.g. array([0.5, 1.5, 2.5, ...]).
    freq : np.ndarray
        The frequency of the spectrogram, e.g. array([0, 1, 2, 3, ...]).
    norm : Normalize
        The normalization object.
    tmin : float
        The minimum time of the spectrogram. It is used to set the x-axis limit so that
        the image only shows the desired time range.
    tmax : float
        The maximum time of the spectrogram. It is used to set the x-axis limit so that
        the image only shows the desired time range.
    """
    cmap = get_cmap()
    pixels_per_bin = 5
    dpi = 100

    w = len(time) * pixels_per_bin / dpi
    h = len(freq) * pixels_per_bin / dpi

    fig, ax = plt.subplots(figsize=(w, h), dpi=dpi)
    ax.imshow(
        specgram,
        aspect="auto",
        norm=norm,
        origin="lower",
        extent=[time.min(), time.max(), freq.min(), freq.max()],
        cmap=cmap,
        interpolation="bicubic",
    )
    ax.set_xlim(tmin, tmax)
    ax.set_ylim(0, freq.max())
    ax.axis("off")
    fig.tight_layout(pad=0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, bbox_inches="tight", pad_inches=0)
    buf.seek(0)
    return buf.read()


class StreamEncoder:
    version: int = 0

    def encode_stream(self, data: StreamData) -> bytes:
        request_id = pad(data.request_id.encode("utf-8"), 64)
        command = pad(data.command.encode("utf-8"), 64)
        channel_id = pad(data.channel_id.encode("utf-8"), 64)

        if data.trace is None or data.trace.stats.npts == 0:
            time = 0
            n_samples = 0
            sampling_rate = 1
            min_value = 0
            max_value = 0
            values = np.zeros(0, dtype=np.float32)
            mask = np.zeros(0, dtype=bool)
            mask_bytes = np.zeros(0, dtype=np.uint8)
        else:
            trace = data.trace
            array = np.ma.masked_array(trace.data)
            values = array.data.astype(np.float32)
            mask = array.mask.astype(bool)

            if mask.shape != values.shape:
                mask = np.zeros(values.shape, dtype=bool)

            n_samples = values.size
            mask_bytes = np.packbits(mask.astype(np.uint8))
            time = trace.stats.starttime.timestamp * 1000
            sampling_rate = trace.stats.sampling_rate
            min_value = np.nanmin(values)
            max_value = np.nanmax(values)

        binary = b""
        binary += struct.pack("<i", self.version)
        binary += request_id
        binary += command
        binary += channel_id
        binary += struct.pack("<qq", data.start, data.end)
        binary += struct.pack("<d", time)
        binary += struct.pack("<f", sampling_rate)
        binary += struct.pack("<i", n_samples)
        binary += struct.pack("<f", min_value)
        binary += struct.pack("<f", max_value)
        binary += values.tobytes()
        binary += mask_bytes.tobytes()

        compressor = zstd.ZstdCompressor()
        compressed = compressor.compress(binary)
        return compressed

    def encode_spectrogram(self, data: SpectrogramData) -> bytes:
        request_id = pad(data.request_id.encode("utf-8"), 64)
        command = pad(data.command.encode("utf-8"), 64)
        channel_id = pad(data.channel_id.encode("utf-8"), 64)
        time_signal = np.arange(data.npoints) / data.sample_rate

        freq_length = len(data.freq)
        if len(data.freq) == 0:
            freq_min = 0
            freq_max = 0
        else:
            freq_min = 0
            freq_max = data.freq.max()

        time_length = len(data.time)
        if len(data.time) == 0:
            time_min = 0
            time_max = 0
        else:
            time_min = data.start
            time_max = data.end

        if len(data.data) == 0:
            min_val = 0
            max_val = 0
            image = b""
        else:
            min_val = data.data.min()
            max_val = data.data.max()
            image = generate_image(
                data.data,
                data.time,
                data.freq,
                data.norm,
                time_signal.min(),
                time_signal.max(),
            )

        binary = b""
        binary += struct.pack("<i", self.version)
        binary += request_id
        binary += command
        binary += channel_id
        binary += struct.pack("<qq", int(data.start), int(data.end))
        binary += struct.pack("<d", time_min)
        binary += struct.pack("<d", time_max)
        binary += struct.pack("<d", freq_min)
        binary += struct.pack("<d", freq_max)
        binary += struct.pack("<i", time_length)
        binary += struct.pack("<i", freq_length)
        binary += struct.pack("<f", min_val)
        binary += struct.pack("<f", max_val)
        binary += image

        compressor = zstd.ZstdCompressor()
        compressed = compressor.compress(binary)
        return compressed
