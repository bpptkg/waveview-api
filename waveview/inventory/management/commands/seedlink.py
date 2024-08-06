from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.inventory.seedlink.run import run_seedlink


class Command(BaseCommand):
    help = "Run the Seedlink client."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("inventory_id", type=str, help="Inventory ID")

    def handle(self, *args: Any, **options: Any) -> None:
        inventory_id = options["inventory_id"]
        run_seedlink(inventory_id)
