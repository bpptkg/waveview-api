import io
import math
from dataclasses import dataclass
from datetime import datetime, timezone

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from django.db import connection
from matplotlib.colors import LinearSegmentedColormap, Normalize
from obspy import read

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel
from waveview.settings import BASE_DIR
from waveview.signal.packet import pad

matplotlib.use("Agg")


def nearest_power_of_two(x: int) -> int:
    a = math.pow(2, math.ceil(np.log2(x)))
    b = math.pow(2, math.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return int(a)
    else:
        return int(b)


def spectrogram(
    data: np.ndarray,
    sample_rate: float,
    per_lap: float = 0.9,
    wlen: float | None = None,
    mult: float | None = 8.0,
    dbscale: bool = False,
    clip: list[float, float] = [0, 1],
    downsample_factor: int = 3,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, Normalize]:
    if not wlen:
        wlen = 128 / sample_rate

    npoints = len(data)
    nfft = int(nearest_power_of_two(int(wlen * sample_rate)))
    if npoints < nfft:
        raise ValueError("Input data too short to compute spectrogram")

    if mult is not None:
        mult = int(nearest_power_of_two(mult))
        mult = mult * nfft
    nlap = int(nfft * float(per_lap))

    data = data - data.mean()
    end = npoints / sample_rate

    specgram, freq, time, _ = plt.specgram(
        data, Fs=sample_rate, NFFT=nfft, pad_to=mult, noverlap=nlap
    )
    if len(time) < 2:
        raise ValueError("Input data too short to compute spectrogram")

    if dbscale:
        specgram = 10 * np.log10(specgram[1:, :])
    else:
        specgram = np.sqrt(specgram[1:, :])
    freq = freq[1:]

    vmin, vmax = clip
    if vmin < 0 or vmax > 1 or vmin >= vmax:
        msg = "Invalid parameters for clip option."
        raise ValueError(msg)
    _range = float(specgram.max() - specgram.min())
    vmin = specgram.min() + vmin * _range
    vmax = specgram.min() + vmax * _range
    norm = Normalize(vmin, vmax, clip=True)

    return specgram, time, freq, norm


@dataclass
class SpectrogramRequestData:
    request_id: str
    channel_id: str
    start: int
    end: int
    width: int
    height: int
    dark_mode: bool

    @classmethod
    def parse_raw(cls, raw: dict) -> "SpectrogramRequestData":
        return cls(
            request_id=raw["requestId"],
            channel_id=raw["channelId"],
            start=raw["start"],
            end=raw["end"],
            width=raw.get("width", 300),
            height=raw.get("height", 150),
            dark_mode=raw.get("darkMode", False),
        )


class BaseSpectrogramAdapter:
    def spectrogram(self, payload: SpectrogramRequestData) -> bytes:
        raise NotImplementedError("spectrogram method must be implemented")


def generate_image(
    specgram: np.ndarray,
    time: np.ndarray,
    freq: np.ndarray,
    norm: Normalize,
) -> bytes:
    colors = [
        (1, 1, 1),  # White
        (0, 0, 1),  # Blue
        (0, 1, 0),  # Green
        (1, 1, 0),  # Yellow
        # (1, 0.5, 0),  # Orange
        (1, 0, 0),  # Red
        # (0.5, 0, 0)  # Dark Red
    ]
    n_bins = 100
    cmap_name = "waveview"
    cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)
    px = 1 / plt.rcParams["figure.dpi"]
    w = len(time) * px
    h = len(freq) * px
    fig, ax = plt.subplots(figsize=(w, h))
    ax.imshow(
        specgram,
        aspect="auto",
        norm=norm,
        origin="lower",
        extent=[time.min(), time.max(), freq.min(), freq.max()],
        cmap=cmap,
    )
    ax.axis("off")
    fig.tight_layout(pad=0)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
    buf.seek(0)
    return buf.read()


@dataclass
class SpectrogramData:
    request_id: str
    channel_id: str
    data: np.ndarray
    time: np.ndarray
    freq: np.ndarray
    start: int
    end: int
    norm: Normalize
    width: int
    height: int
    command: str = "stream.spectrogram"

    def encode(self) -> bytes:
        request_id = pad(self.request_id.encode("utf-8"), 64)
        command = pad(self.command.encode("utf-8"), 64)
        channel_id = pad(self.channel_id.encode("utf-8"), 64)
        start = self.start
        end = self.end
        if len(self.freq) == 0:
            freqMin = 0
            freqMax = 0
        else:
            freqMin = self.freq.min()
            freqMax = self.freq.max()
        timeLength = len(self.time)
        freqLength = len(self.freq)
        if len(self.data) == 0:
            minVal = 0
            maxVal = 0
            image = b""
        else:
            minVal = self.data.min()
            maxVal = self.data.max()
            image = generate_image(self.data, self.time, self.freq, self.norm)
        header = np.array(
            [
                int(self.start),
                int(self.end),
                start,
                end,
                freqMin,
                freqMax,
                timeLength,
                freqLength,
                minVal,
                maxVal,
            ],
            dtype=np.float64,
        ).tobytes()

        return b"".join(
            [
                request_id,
                command,
                channel_id,
                header,
                image,
            ]
        )


class DummySpectrogramAdapter(BaseSpectrogramAdapter):
    def spectrogram(self, payload: SpectrogramRequestData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        width = payload.width
        height = payload.height

        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)

        fixtures_dir = BASE_DIR / "fixtures"
        filename = fixtures_dir / f"sample.mseed"
        st = read(str(filename))
        data = st[0].data
        sample_rate = st[0].stats.sampling_rate

        try:
            specgram, time, freq, norm = spectrogram(data, sample_rate)
        except ValueError:
            specgram = np.array([], dtype=np.float64)
            time = np.array([], dtype=np.float64)
            freq = np.array([], dtype=np.float64)
            norm = Normalize(0, 1)

        packet = SpectrogramData(
            request_id=request_id,
            channel_id=channel_id,
            data=specgram,
            time=time,
            freq=freq,
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            norm=norm,
            width=width,
            height=height,
        )

        return packet.encode()


class TimescaleSpectrogramAdapter(BaseSpectrogramAdapter):
    def __init__(self) -> None:
        self.datastream = DataStream(connection=connection)

    def spectrogram(self, payload: SpectrogramRequestData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        width = payload.width
        height = payload.height

        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)

        empty_packet = SpectrogramData(
            request_id=request_id,
            channel_id=channel_id,
            data=np.array([]),
            time=np.array([]),
            freq=np.array([]),
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            norm=Normalize(0, 1),
            width=width,
            height=height,
        )

        try:
            Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            return empty_packet.encode()

        st = self.datastream.get_waveform(channel_id, start, end)
        if len(st) == 0:
            return empty_packet.encode()
        data = st[0].data
        if len(data) == 0:
            return empty_packet.encode()
        sample_rate = st[0].stats.sampling_rate

        try:
            specgram, time, freq, norm = spectrogram(data, sample_rate)
        except ValueError:
            specgram = np.array([], dtype=np.float64)
            time = np.array([], dtype=np.float64)
            freq = np.array([], dtype=np.float64)
            norm = Normalize(0, 1)

        packet = SpectrogramData(
            request_id=request_id,
            channel_id=channel_id,
            data=specgram,
            time=time,
            freq=freq,
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            norm=norm,
            width=width,
            height=height,
        )
        return packet.encode()


def get_spectrogram_adapter() -> BaseSpectrogramAdapter:
    return TimescaleSpectrogramAdapter()
