import io
import unittest
import uuid
from datetime import timedelta

import numpy as np
from django.db import connection
from obspy import Stream, Trace, read

from waveview.inventory.db.schema import TimescaleSchemaEditor
from waveview.inventory.datastream import mergebuffer, preparebuffer
from waveview.settings import BASE_DIR


class DataStreamIOTest(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = TimescaleSchemaEditor(connection=connection)
        self.table = f"datastream_{uuid.uuid4().hex}"
        self.print_info = False

    def tearDown(self) -> None:
        self.schema.drop_table(self.table)

    def test_io(self) -> None:
        self.schema.create_table(self.table)
        self.schema.create_hypertable(self.table)
        is_table_created = self.schema.assert_table_exists(self.table)
        self.assertTrue(is_table_created)

        path = str(BASE_DIR / "fixtures" / "sample.mseed")
        reclen = 512
        chunksize = reclen

        npts = 0
        uncompressed = 0
        compressed = 0
        with io.open(path, "rb") as f:
            while True:
                with io.BytesIO() as chunk:
                    c = f.read(chunksize)
                    if not c:
                        break
                    chunk.write(c)
                    chunk.seek(0, 0)
                    stream = read(chunk)

                for trace in stream:
                    trace: Trace
                    st, et, sr, dtype, buf = preparebuffer(trace)
                    self.schema.insert(self.table, st, et, sr, dtype, buf)
                    npts += len(trace.data)
                    compressed += len(buf)
                    uncompressed += trace.data.nbytes

                    if self.print_info:
                        print(trace)

        st: Stream = read(path)
        qst = st[0].stats.starttime.datetime + timedelta(seconds=-10)
        qet = st[-1].stats.endtime.datetime + timedelta(seconds=10)
        rows = self.schema.query(self.table, qst, qet)
        data = mergebuffer(rows)

        tr: Trace = st[0]
        self.assertEqual(len(tr.data), len(data))
        self.assertTrue(np.array_equal(tr.data, data))

        compression_ratio = (compressed / uncompressed) * 100
        if self.print_info:
            print("Original Trace:", tr)
            print("Total data points:", npts)
            print("Uncompressed size:", uncompressed, "bytes")
            print("Compressed size:", compressed, "bytes")
            print("Compression ratio:", compression_ratio, "%")
