from datetime import datetime

import psycopg2


class TimescaleQuery:
    sql_query_table = (
        "SELECT time, value FROM {table} WHERE time >= '{start}' AND time <= '{end}'"
    )
    sql_query_table_lttb = "SELECT time, value FROM unnest((SELECT lttb(time, value, {max_points}) FROM {table})) WHERE time >= '{start}' AND time <= '{end}'"

    def __init__(self, connection: psycopg2.extensions.connection) -> None:
        self.connection = connection

    def fetch(
        self, start: datetime | int, end: datetime | int, table: str
    ) -> list[tuple[datetime, float]]:
        if isinstance(start, int):
            start = datetime.fromtimestamp(start)
        if isinstance(end, int):
            end = datetime.fromtimestamp(end)

        with self.connection.cursor() as cursor:
            cursor.execute(
                self.sql_query_table.format(
                    table=table,
                    start=start.isoformat(),
                    end=end.isoformat(),
                )
            )
            return cursor.fetchall()

    def fetch_lttb(
        self, start: datetime | int, end: datetime | int, table: str, max_points: int
    ) -> list[tuple[datetime, float]]:
        if isinstance(start, int):
            start = datetime.fromtimestamp(start)
        if isinstance(end, int):
            end = datetime.fromtimestamp(end)

        with self.connection.cursor() as cursor:
            cursor.execute(
                self.sql_query_table_lttb.format(
                    table=table,
                    start=start.isoformat(),
                    end=end.isoformat(),
                    max_points=int(max_points),
                )
            )
            return cursor.fetchall()
