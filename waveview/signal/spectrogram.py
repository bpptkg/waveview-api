import math
from dataclasses import dataclass
from datetime import datetime, timezone

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from obspy import read
from scipy.signal import resample

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

    specgram = resample(specgram, specgram.shape[0] // downsample_factor, axis=0)
    specgram = resample(specgram, specgram.shape[1] // downsample_factor, axis=1)
    time = resample(time, len(time) // downsample_factor)
    freq = resample(freq, len(freq) // downsample_factor)

    return specgram, time, freq, norm


@dataclass
class SpectrogramRequestData:
    request_id: str
    channel_id: str
    start: int
    end: int

    @classmethod
    def parse_raw(cls, raw: dict) -> "SpectrogramRequestData":
        return cls(
            request_id=raw["requestId"],
            channel_id=raw["channelId"],
            start=raw["start"],
            end=raw["end"],
        )


class BaseSpectrogramAdapter:
    def spectrogram(self, payload: SpectrogramRequestData) -> bytes:
        raise NotImplementedError("spectrogram method must be implemented")


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
    command: str = "stream.spectrogram"

    def encode(self) -> bytes:
        request_id = pad(self.request_id.encode("utf-8"), 64)
        command = pad(self.command.encode("utf-8"), 64)
        channel_id = pad(self.channel_id.encode("utf-8"), 64)
        timeMin = self.time.min()
        timeMax = self.time.max()
        freqMin = self.freq.min()
        freqMax = self.freq.max()
        timeLength = len(self.time)
        freqLength = len(self.freq)
        minVal = self.data.min()
        maxVal = self.data.max()
        header = np.array(
            [
                int(self.start),
                int(self.end),
                timeMin,
                timeMax,
                freqMin,
                freqMax,
                timeLength,
                freqLength,
                minVal,
                maxVal,
            ],
            dtype=np.float64,
        )
        specgram = self.data.flatten().astype(np.float64)
        return b"".join(
            [
                request_id,
                command,
                channel_id,
                header.tobytes(),
                specgram.tobytes(),
            ]
        )


class DummySpectrogramAdapter(BaseSpectrogramAdapter):
    def spectrogram(self, payload: SpectrogramRequestData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id

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

        packet = SpectrogramData(
            request_id=request_id,
            channel_id=channel_id,
            data=np.flipud(specgram),
            time=time,
            freq=freq,
            start=start.timestamp() * 1000,
            end=end.timestamp() * 1000,
            norm=norm,
        )
        return packet.encode()


def get_spectrogram_adapter() -> BaseSpectrogramAdapter:
    return DummySpectrogramAdapter()
