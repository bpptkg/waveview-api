import tempfile
import unittest
import uuid
from datetime import timedelta

from django.db import connection
from obspy import Stream, UTCDateTime

from waveview.data.sample import get_sample_waveform
from waveview.inventory.datastream import DataStream, build_trace
from waveview.inventory.db.schema import TimescaleSchemaEditor


class TestStreamGap(unittest.TestCase):
    def test_stream_gap(self) -> None:
        schema = TimescaleSchemaEditor(connection=connection)
        table = f"datastream_{uuid.uuid4().hex}"
        schema.create_table(table)
        is_table_created = schema.assert_table_exists(table)
        self.assertTrue(is_table_created)

        st = get_sample_waveform()
        self.assertEqual(len(st.get_gaps()), 0)
        tr = st[0].copy()
        t = UTCDateTime("2024-06-11T10:30:20")
        st[0].trim(endtime=t)
        tr.trim(starttime=t + 1)
        st.append(tr)
        self.assertEqual(len(st.get_gaps()), 1)

        path = tempfile.gettempdir() + "/temp.mseed"
        st.merge(method=1, fill_value=0)
        st.write(path, format="MSEED")

        datastream = DataStream(connection)
        datastream.load_stream(table, path)

        start = st[0].stats.starttime.datetime - timedelta(hours=1)
        end = st[0].stats.endtime.datetime + timedelta(hours=1)
        rows = schema.query(table, start, end)

        lst = Stream(
            traces=[
                build_trace(
                    row=row,
                    network=st[0].stats.network,
                    station=st[0].stats.station,
                    location=st[0].stats.location,
                    channel=st[0].stats.channel,
                )
                for row in rows
            ]
        )
        lst.merge(method=1, fill_value=0)

        self.assertEqual(len(lst), len(st))
        self.assertEqual(len(lst.get_gaps()), 0)
        self.assertEqual(lst[0].stats.starttime, st[0].stats.starttime)
        self.assertEqual(lst[0].stats.endtime, st[0].stats.endtime)
        self.assertEqual(lst[0].stats.sampling_rate, st[0].stats.sampling_rate)
        self.assertEqual(lst[0].stats.npts, st[0].stats.npts)

        schema.drop_table(table)


if __name__ == "__main__":
    unittest.main()
