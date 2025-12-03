import unittest
import uuid
import zlib
from datetime import timedelta

import numpy as np
import pytest
from django.db import connection
from django.utils import timezone

from waveview.inventory.db.schema import TimescaleSchemaEditor


@pytest.mark.django_db
class TimescaleQueryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = TimescaleSchemaEditor(connection=connection)
        self.table = f"datastream_{uuid.uuid4().hex}"

    def tearDown(self) -> None:
        self.schema.drop_table(self.table)

    def test_query(self) -> None:
        self.schema.create_table(self.table)
        self.schema.create_hypertable(self.table)
        is_table_created = self.schema.assert_table_exists(self.table)
        self.assertTrue(is_table_created)

        sample_rate = 100
        npts = 1000
        start = timezone.now() - timedelta(minutes=5)
        end = start + timedelta(seconds=npts / sample_rate)
        data = np.random.rand(npts).astype(np.int32)
        cdata = zlib.compress(data.tobytes())
        self.schema.insert(self.table, start, end, sample_rate, "int32", cdata)

        qst = start - timedelta(seconds=10)
        qet = end + timedelta(seconds=10)
        result = self.schema.query(self.table, qst, qet)
        self.assertEqual(len(result), 1)

        [st, et, sr, dtype, buf] = result[0]
        self.assertEqual(st, start)
        self.assertEqual(et, end)
        self.assertEqual(sr, sample_rate)
        self.assertEqual(dtype, "int32")

        dtrace = zlib.decompress(buf)
        trace = np.frombuffer(dtrace, dtype=np.int32)
        self.assertTrue(np.array_equal(data, trace))


if __name__ == "__main__":
    unittest.main()
