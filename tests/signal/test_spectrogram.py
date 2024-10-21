import time
import unittest
import uuid

import numpy as np
from obspy import Stream, read

from waveview.data.sample import get_sample_file_path
from waveview.signal.spectrogram import SpectrogramData, spectrogram


class SpectrogramTest(unittest.TestCase):
    def test_spectrogram(self) -> None:
        path = get_sample_file_path("sample.mseed")
        st: Stream = read(path)

        data = st[0].data
        sample_rate = st[0].stats.sampling_rate
        specgram, ts, fs, norm = spectrogram(data, sample_rate)

        uid = str(uuid.uuid4())
        packet = SpectrogramData(
            request_id=uid,
            channel_id=uid,
            data=np.flipud(specgram),
            time=ts,
            freq=fs,
            start=time.time() * 1000,
            end=time.time() * 1000,
            norm=norm,
            npoints=len(data),
            sample_rate=sample_rate,
            width=800,
            height=600,
        )
        data = packet.encode()
        self.assertTrue(isinstance(data, bytes))


if __name__ == "__main__":
    unittest.main()
