import unittest

from waveview.contrib.sinoas.channels import WinstonChannel
from waveview.contrib.sinoas.fetcher import Fetcher, build_rsam_url


class FetcherTest(unittest.TestCase):
    def test_build_rsam_url(self) -> None:
        code = WinstonChannel.VG_MEPAS_HHZ
        url = build_rsam_url(code)
        self.assertEqual(
            url, f"http://127.0.0.1:16030/rsam/?code={code}&t1=-0.0006&rsamP=1&csv=1"
        )

    def test_fetch(self) -> None:
        fetcher = Fetcher()
        csv = "2024-10-22 04:41:30,930.2862,\n2024-10-22 04:41:31,486.569267,\n"
        df = fetcher.process_csv(csv)
        self.assertEqual(len(df), 1)


if __name__ == "__main__":
    unittest.main()
