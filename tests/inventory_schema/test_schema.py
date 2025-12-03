import unittest
import uuid

import pytest
from django.db import connection

from waveview.inventory.db.schema import TimescaleSchemaEditor


@pytest.mark.django_db
class TestTimescaleSchemaEditor(unittest.TestCase):
    def setUp(self):
        self.schema_editor = TimescaleSchemaEditor(connection=connection)

    def test_create_table(self) -> None:
        table = f"datastream_{uuid.uuid4().hex}"
        self.schema_editor.create_table(table)
        is_table_created = self.schema_editor.assert_table_exists(table)
        self.assertTrue(is_table_created)

        self.schema_editor.drop_table(table)

    def test_create_hypertable(self) -> None:
        table_name = f"datastream_{uuid.uuid4().hex}"
        self.schema_editor.create_table(table_name)
        self.schema_editor.create_hypertable(table_name)
        is_table_created = self.schema_editor.assert_table_exists(table_name)
        self.assertTrue(is_table_created)

        self.schema_editor.drop_table(table_name)

    def test_drop_table(self):
        table_name = f"datastream_{uuid.uuid4().hex}"
        self.schema_editor.create_table(table_name)
        is_table_created = self.schema_editor.assert_table_exists(table_name)
        self.assertTrue(is_table_created)

        self.schema_editor.drop_table(table_name)
        is_table_created = self.schema_editor.assert_table_exists(table_name)
        self.assertFalse(is_table_created)


if __name__ == "__main__":
    unittest.main()
