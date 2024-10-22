import unittest
from datetime import datetime, timedelta
import pandas as pd
from waveview.contrib.sinoas.detector import Detector


class DetectorTest(unittest.TestCase):
    def setUp(self):
        self.detector = Detector()

    def test_detect_no_event(self) -> None:
        # Create a DataFrame with no event
        data = {
            "time": [datetime.now() - timedelta(seconds=i) for i in range(3)],
            "rsam": [100, 200, 300],
        }
        df = pd.DataFrame(data)
        self.detector.detect(df)
        self.assertFalse(self.detector.triggered)

    def test_detect_event(self) -> None:
        # Create a DataFrame with an event
        data = {
            "time": [datetime.now() - timedelta(seconds=i) for i in range(3)],
            "rsam": [3100, 3200, 3300],
        }
        df = pd.DataFrame(data)
        self.detector.detect(df)
        self.assertTrue(self.detector.triggered)
        self.assertEqual(self.detector.mepas_rsam, 3200)

    def test_reset(self) -> None:
        # Trigger an event and then reset
        data = {
            "time": [datetime.now() - timedelta(seconds=i) for i in range(3)],
            "rsam": [3100, 3200, 3300],
        }
        df = pd.DataFrame(data)
        self.detector.detect(df)
        self.detector.reset()
        self.assertFalse(self.detector.triggered)
        self.assertIsNone(self.detector.time)
        self.assertEqual(self.detector.duration, 0)
        self.assertEqual(self.detector.mepas_rsam, 0)


if __name__ == "__main__":
    unittest.main()
