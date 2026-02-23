from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.inventory.models import InventoryFile
from waveview.inventory.stationxml import print_info


class Command(BaseCommand):
    help = "Print info of station XML files."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "path", nargs="?", default=None, help="Path to the station XML file"
        )
        parser.add_argument(
            "--inventory-file-id",
            "-i",
            dest="inventory_file_id",
            help="ID of the inventory file",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        path = options["path"]
        print(f"Path: {path}")
        if Path(path).is_file():
            print_info(path)

        inventory_file_id = options["inventory_file_id"]
        if inventory_file_id is not None:
            try:
                inventory_file = InventoryFile.objects.get(pk=inventory_file_id)
                print(f"Inventory file: {inventory_file.file.path}")
                print_info(inventory_file.file.path)
            except InventoryFile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Inventory file with id {inventory_file_id} does not exist"
                    )
                )
