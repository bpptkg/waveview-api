import unittest
from pathlib import Path

from waveview.contrib.btbb.reader import ResultReader


class BTBBResultReaderTest(unittest.TestCase):
    def test_read(self) -> None:
        path = Path(__file__).parent / "result.dat"
        reader = ResultReader()
        results = reader.read(path)
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(len(item["phases"]), 6)
        self.assertEqual(item["header"]["TS"], "20241203_0053A")
        self.assertEqual(item["phases"][0]["sta"], "MEGRA")
        self.assertEqual(item["phases"][1]["sta"], "MEKLA")
        self.assertEqual(item["phases"][2]["sta"], "MEKLS")
        self.assertEqual(item["phases"][3]["sta"], "MELAB")
        self.assertEqual(item["phases"][4]["sta"], "MEPAS")
        self.assertEqual(item["phases"][5]["sta"], "MEPSL")


if __name__ == "__main__":
    unittest.main()
