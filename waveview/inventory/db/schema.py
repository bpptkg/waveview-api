from datetime import datetime

import psycopg2
from django.db import ProgrammingError
from django.db.backends.postgresql.schema import DatabaseSchemaEditor


class TimescaleSchemaEditor(DatabaseSchemaEditor):
    sql_create_model = (
        "CREATE TABLE {table} ("
        "st TIMESTAMPTZ UNIQUE,"
        "et TIMESTAMPTZ,"
        "sr DOUBLE PRECISION,"
        "dtype VARCHAR,"
        "buf BYTEA"
        ")"
    )
    sql_create_hypertable = (
        "SELECT create_hypertable('{table}', by_range('st', 86400000000))"
    )
    sql_drop_table = "DROP TABLE {table} CASCADE"
    sql_table_exists = "SELECT * FROM {table} LIMIT 1"
    sql_insert = "INSERT INTO {table} (st, et, sr, dtype, buf) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (st) DO UPDATE SET et = EXCLUDED.et, sr = EXCLUDED.sr, dtype = EXCLUDED.dtype, buf = EXCLUDED.buf"
    sql_is_table_exists = (
        "SELECT * FROM information_schema.tables WHERE table_name = '{table}'"
    )
    sql_query_table = "SELECT st, et, sr, dtype, buf FROM {table} WHERE st >= '{start}' AND et < '{end}' ORDER BY st"
    sql_hypertable_size = "SELECT hypertable_size('{table}')"

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

    def is_table_exists(self, table: str) -> bool:
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_is_table_exists.format(table=table))
            return cursor.fetchone() is not None

    def insert(
        self, table: str, st: datetime, et: datetime, sr: float, dtype: str, buf: bytes
    ) -> None:
        self.execute(
            self.sql_insert.format(
                table=self.quote_name(table),
            ),
            params=(st.isoformat(), et.isoformat(), sr, dtype, buf),
        )

    def query(
        self, table: str, start: datetime | int, end: datetime | int
    ) -> list[tuple[datetime, datetime, float, str, bytes]]:
        if isinstance(start, int):
            start = datetime.fromtimestamp(start)
        if isinstance(end, int):
            end = datetime.fromtimestamp(end)

        self.connection: psycopg2.extensions.connection
        with self.connection.cursor() as cursor:
            cursor.execute(
                self.sql_query_table.format(
                    table=table,
                    start=start.isoformat(),
                    end=end.isoformat(),
                )
            )
            return cursor.fetchall()

    def hypertable_size(self, table: str) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(self.sql_hypertable_size.format(table=table))
            return cursor.fetchone()[0]
