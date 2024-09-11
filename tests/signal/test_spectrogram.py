import time
import unittest
import uuid

import numpy as np
from django.conf import settings
from obspy import Stream, read

from waveview.signal.spectrogram import SpectrogramData, spectrogram


class SpectrogramTest(unittest.TestCase):
    def test_spectrogram(self) -> None:
        path = str(settings.BASE_DIR / "fixtures" / "sample.mseed")
        st: Stream = read(path)
        print("Stream:", st)

        data = st[0].data
        sample_rate = st[0].stats.sampling_rate
        t1 = time.time()
        specgram, ts, fs, norm = spectrogram(data, sample_rate)
        t2 = time.time()
        print(f"Spectrogram benchmark: {t2-t1} seconds")

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
        )
        nbytes = len(packet.encode())
        print(f"Packet size: {nbytes} bytes")


if __name__ == "__main__":
    unittest.main()
