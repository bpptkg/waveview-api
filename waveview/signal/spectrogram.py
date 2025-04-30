import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
from django.db import connection
from matplotlib.colors import Normalize
from scipy.interpolate import interp1d
from scipy.signal import get_window
from scipy.signal import spectrogram as scipy_spectrogram

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel
from waveview.signal.encoder import SpectrogramData, StreamEncoder

logger = logging.getLogger(__name__)


def nearest_power_of_two(x: int) -> int:
    a = math.pow(2, math.ceil(np.log2(x)))
    b = math.pow(2, math.floor(np.log2(x)))
    if abs(a - x) < abs(b - x):
        return int(a)
    else:
        return int(b)


def interpolate_gaps(data: np.ndarray, threshold: float = 1e-12) -> np.ndarray:
    """Interpolate over gaps (values near zero)."""
    x = np.arange(len(data))
    mask = np.abs(data) > threshold
    if np.sum(mask) < 2:
        raise ValueError("Not enough valid data to interpolate.")
    f = interp1d(x[mask], data[mask], kind="linear", fill_value="extrapolate")
    return f(x)


def _nearest_pow_2(x: float) -> int:
    """Find the nearest power of 2 greater than or equal to x."""
    return 1 << (int(x) - 1).bit_length()


def spectrogram(
    data: np.ndarray,
    sample_rate: float,
    per_lap: float = 0.9,
    wlen: float | None = None,
    mult: float | None = 8.0,
    dbscale: bool = False,
    clip: list[float] = [0.0, 1.0],
    gap_threshold: float = 1e-12,
    freqmax: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, Normalize]:
    """Compute a spectrogram (ObsPy-like) with gap handling and scaling."""

    data = interpolate_gaps(data, threshold=gap_threshold)
    data = data - np.mean(data)

    if wlen is None:
        wlen = 128 / sample_rate

    nfft = int(_nearest_pow_2(wlen * sample_rate))
    if len(data) < nfft:
        raise ValueError("Input data too short to compute spectrogram.")

    # Pad to smoother output.
    if mult is not None:
        mult = int(_nearest_pow_2(mult)) * nfft
    nlap = int(nfft * per_lap)

    window = get_window("hann", nfft)

    # Compute spectrogram using scipy.
    freq, time, Sxx = scipy_spectrogram(
        data,
        fs=sample_rate,
        nperseg=nfft,
        noverlap=nlap,
        nfft=nfft,
        scaling="density",
        mode="psd",
        window=window,
    )

    # Discard DC component.
    freq = freq[1:]
    Sxx = Sxx[1:, :]

    # Rescale to desired frequency range.
    if freqmax is not None:
        freq_mask = freq <= freqmax
        freq = freq[freq_mask]
        Sxx = Sxx[freq_mask, :]

    # Apply db or sqrt scale.
    with np.errstate(divide="ignore"):
        if dbscale:
            Sxx = 10 * np.log10(Sxx)
        else:
            Sxx = np.sqrt(Sxx)

    # Clip based on amplitude percentiles.
    vmin_pct, vmax_pct = clip
    if not (0 <= vmin_pct < vmax_pct <= 1):
        raise ValueError("Clip values must be between 0 and 1 and vmin < vmax.")
    _range = Sxx.max() - Sxx.min()
    vmin = Sxx.min() + vmin_pct * _range
    vmax = Sxx.min() + vmax_pct * _range
    norm = Normalize(vmin=vmin, vmax=vmax, clip=True)

    return Sxx, time, freq, norm


@dataclass
class SpectrogramRequestData:
    request_id: str
    channel_id: str
    start: int
    end: int
    width: int
    height: int
    resample: bool
    sample_rate: int
    freqmax: float | None = None

    @classmethod
    def from_raw_data(cls, raw: dict) -> "SpectrogramRequestData":
        start = raw["start"]
        end = raw["end"]
        return cls(
            request_id=raw["requestId"],
            channel_id=raw["channelId"],
            start=int(start),
            end=int(end),
            resample=raw.get("resample", True),
            sample_rate=raw.get("sampleRate", 1),
            width=raw.get("width", 300),
            height=raw.get("height", 150),
            freqmax=raw.get("freqMax", 25),
        )


class BaseSpectrogramAdapter:
    def spectrogram(self, payload: SpectrogramRequestData) -> bytes:
        raise NotImplementedError("spectrogram method must be implemented")


class TimescaleSpectrogramAdapter(BaseSpectrogramAdapter):
    def __init__(self) -> None:
        self.datastream = DataStream(connection=connection)

    def spectrogram(self, payload: SpectrogramRequestData) -> bytes:
        request_id = payload.request_id
        channel_id = payload.channel_id
        width = payload.width
        height = payload.height
        freqmax = payload.freqmax

        start = datetime.fromtimestamp(payload.start / 1000, timezone.utc)
        end = datetime.fromtimestamp(payload.end / 1000, timezone.utc)

        encoder = StreamEncoder()
        empty = encoder.encode_spectrogram(
            SpectrogramData(
                request_id=request_id,
                channel_id=channel_id,
                npoints=0,
                sample_rate=1,
                data=np.array([]),
                time=np.array([]),
                freq=np.array([]),
                start=start.timestamp() * 1000,
                end=end.timestamp() * 1000,
                norm=Normalize(0, 1),
                width=width,
                height=height,
            )
        )

        try:
            Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            return empty

        st = self.datastream.get_waveform(channel_id, start, end)
        st.merge(method=0, fill_value=None)

        if len(st) == 0 or len(st[0].data) == 0:
            return empty

        trace = st[0]
        data = trace.data
        sample_rate = trace.stats.sampling_rate
        starttime = trace.stats.starttime
        npts = trace.stats.npts
        delta = trace.stats.delta
        endtime = starttime + npts * delta

        try:
            specgram, time, freq, norm = spectrogram(data, sample_rate, freqmax=freqmax)
        except ValueError as e:
            logger.error(f"Error computing spectrogram: {e}")
            return empty

        # If signal is resampled, update the start and end time of the signal as
        # the original start and end time of the signal will be different after
        # resampling. Therefore, the spectrogram coordinates need to be updated
        # as well.
        if payload.resample:
            st.resample(payload.sample_rate)
            sample_rate = payload.sample_rate
            starttime = st[0].stats.starttime
            npts = st[0].stats.npts
            delta = st[0].stats.delta
            endtime = starttime + npts * delta
            data = st[0].data

        return encoder.encode_spectrogram(
            SpectrogramData(
                request_id=request_id,
                channel_id=channel_id,
                npoints=npts,
                sample_rate=sample_rate,
                data=specgram,
                time=time,
                freq=freq,
                start=starttime.timestamp * 1000,
                end=endtime.timestamp * 1000,
                norm=norm,
                width=width,
                height=height,
            )
        )


def get_spectrogram_adapter() -> BaseSpectrogramAdapter:
    return TimescaleSpectrogramAdapter()
