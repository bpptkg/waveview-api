from datetime import datetime

from django.db import ProgrammingError
from django.db.backends.postgresql.schema import DatabaseSchemaEditor


class TimescaleSchemaEditor(DatabaseSchemaEditor):
    sql_create_model = (
        "CREATE TABLE {table} ("
        "time TIMESTAMPTZ NOT NULL UNIQUE,"
        "value DOUBLE PRECISION NULL"
        ")"
    )
    sql_create_hypertable = (
        "SELECT create_hypertable('{table}', by_range('time', 86400000000))"
    )
    sql_drop_table = "DROP TABLE {table} CASCADE"
    sql_table_exists = "SELECT * FROM {table} LIMIT 1"
    sql_bulk_insert = "INSERT INTO {table} (time, value) VALUES {values}"
    sql_bulk_upsert = "INSERT INTO {table} (time, value) VALUES {values} ON CONFLICT (time) DO UPDATE SET value = EXCLUDED.value"
    sql_table_size = "SELECT pg_total_relation_size('{table}')"
    sql_is_table_exists = (
        "SELECT * FROM information_schema.tables WHERE table_name = '{table}'"
    )

    def create_table(self, table: str) -> None:
        self.execute(self.sql_create_model.format(table=self.quote_name(table)))

    def create_hypertable(self, table: str) -> None:
        self.execute(self.sql_create_hypertable.format(table=table))

    def drop_table(self, table: str) -> None:
        self.execute(self.sql_drop_table.format(table=self.quote_name(table)))

    def assert_table_exists(self, table: str) -> bool:
        try:
            self.execute(self.sql_table_exists.format(table=self.quote_name(table)))
            return True
        except ProgrammingError:
            return False

    def bulk_insert(
        self, table: str, times: list[datetime], values: list[float]
    ) -> None:
        self.execute(
            self.sql_bulk_insert.format(
                table=self.quote_name(table),
                values=", ".join(
                    f"'({t.isoformat()}', {v})" for t, v in zip(times, values)
                ),
            )
        )

    def bulk_upsert(
        self, table: str, times: list[datetime], values: list[float]
    ) -> None:
        self.execute(
            self.sql_bulk_upsert.format(
                table=self.quote_name(table),
                values=", ".join(
                    f"('{t.isoformat()}', {v})" for t, v in zip(times, values)
                ),
            )
        )

    def table_size(self, table: str) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_table_size.format(table=(table)))
            return cursor.fetchone()[0]

    def is_table_exists(self, table: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_is_table_exists.format(table=table))
            return cursor.fetchone() is not None
