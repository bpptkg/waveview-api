import unittest
import uuid

import pytest
from django.db import connection

from waveview.inventory.db.schema import TimescaleSchemaEditor


@pytest.mark.django_db
class TestTimescaleSchemaEditor(unittest.TestCase):
    def setUp(self):
        self.schema_editor = TimescaleSchemaEditor(connection=connection)

    def test_table_size(self) -> None:
        table = f"datastream_{uuid.uuid4().hex}"
        self.schema_editor.create_table(table)
        self.schema_editor.create_hypertable(table)
        size = self.schema_editor.hypertable_size(table)
        self.assertIsInstance(size, int)

        self.schema_editor.drop_table(table)


if __name__ == "__main__":
    unittest.main()
