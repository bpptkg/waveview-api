from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.inventory.seedlink.run import run_seedlink
from waveview.organization.models import Organization


class Command(BaseCommand):
    help = "Run the Seedlink client."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("organization_slug", type=str, help="Organization slug.")
        parser.add_argument("--debug", action="store_true", help="Debug mode.")

    def handle(self, *args: Any, **options: Any) -> None:
        organization_slug = options["organization_slug"]
        debug = options["debug"]

        try:
            organization = Organization.objects.get(slug=organization_slug)
        except Organization.DoesNotExist:
            self.stderr.write(
                f"Organization with slug '{organization_slug}' does not exist."
            )
            return
        inventory_id = str(organization.inventory.id)
        run_seedlink(inventory_id, debug=debug)
