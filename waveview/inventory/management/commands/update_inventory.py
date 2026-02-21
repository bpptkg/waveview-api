from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.inventory.models import InventoryFile
from waveview.tasks.update_inventory import update_inventory


class Command(BaseCommand):
    help = "Update inventory of all station xml."

    def add_arguments(self, parser: CommandParser) -> None:
        pass

    def handle(self, *args: Any, **options: Any) -> None:
        for f in InventoryFile.objects.order_by("name").all():
            self.stdout.write(f"Updating inventory {f.name}...")
            update_inventory(str(f.id))
