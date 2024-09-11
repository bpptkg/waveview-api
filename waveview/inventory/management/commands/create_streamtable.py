import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import connection

from waveview.inventory.db.schema import TimescaleSchemaEditor


class Command(BaseCommand):
    help = "Creata a table to store stream data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("name", type=str, help="Table name to store the data.")
        parser.add_argument(
            "--unique",
            action="store_true",
            help="Append unique UUID to the table name.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        name: str = options["name"]
        unique: bool = options["unique"]
        if unique:
            name = f"{name}_{uuid.uuid4().hex}"
        schema = TimescaleSchemaEditor(connection)
        schema.create_table(name)
        schema.create_hypertable(name)
        is_table_created = schema.assert_table_exists(name)
        if is_table_created:
            self.stdout.write(self.style.SUCCESS(f"Table {name} is created."))
        else:
            self.stderr.write(self.style.ERROR(f"Table {name} is not created."))
