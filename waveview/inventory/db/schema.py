from django.db import ProgrammingError
from django.db.backends.postgresql.schema import DatabaseSchemaEditor


class TimescaleSchemaEditor(DatabaseSchemaEditor):
    sql_create_model = (
        'CREATE TABLE "{table}" ('
        "time TIMESTAMPTZ NOT NULL,"
        "value DOUBLE PRECISION NULL"
        ")"
    )
    sql_create_hypertable = (
        "SELECT create_hypertable('\"{table}\"', by_range('{time_column}'))"
    )
    sql_drop_table = 'DROP TABLE "{table}" CASCADE'
    sql_table_exists = 'SELECT * FROM "{table}" LIMIT 1'

    def create_table(self, table: str) -> None:
        self.execute(self.sql_create_model.format(table=table))

    def create_hypertable(self, table: str, time_column: str) -> None:
        self.execute(
            self.sql_create_hypertable.format(table=table, time_column=time_column)
        )

    def drop_table(self, table: str) -> None:
        self.execute(self.sql_drop_table.format(table=table))

    def assert_table_exists(self, table: str) -> bool:
        try:
            self.execute(self.sql_table_exists.format(table=table))
            return True
        except ProgrammingError:
            return False
