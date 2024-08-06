import random
import unittest
import uuid
from datetime import datetime, timedelta

from django.db import connection

from waveview.inventory.db.query import TimescaleQuery
from waveview.inventory.db.schema import TimescaleSchemaEditor


class TimescaleQueryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.schema_editor = TimescaleSchemaEditor(connection=connection)
        self.query = TimescaleQuery(connection=connection)
        self.table = f"datastream_{uuid.uuid4().hex}"

    def tearDown(self) -> None:
        self.schema_editor.drop_table(self.table)

    def test_query(self) -> None:
        self.schema_editor.create_table(self.table)
        self.schema_editor.create_hypertable(self.table)
        is_table_created = self.schema_editor.assert_table_exists(self.table)
        self.assertTrue(is_table_created)

        start = datetime.now()
        times = [start + timedelta(seconds=i) for i in range(1000)]
        values = [random.random() for _ in range(100)]
        self.schema_editor.bulk_upsert(self.table, times, values)

        result = self.query.fetch(start, start + timedelta(seconds=100), self.table)
        self.assertEqual(len(result), 100)

        result = self.query.fetch_lttb(
            start, start + timedelta(seconds=100), self.table, 10
        )
        self.assertEqual(len(result), 10)


if __name__ == "__main__":
    unittest.main()
