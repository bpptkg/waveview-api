from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.contrib.sinoas.adapter import run_sinoas
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano


class Command(BaseCommand):
    help = "Run the SINOAS event detection."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("organization_slug", type=str, help="Organization slug.")
        parser.add_argument("volcano_slug", type=str, help="Volcano slug.")

    def handle(self, *args: Any, **options: Any) -> None:
        organization_slug = options["organization_slug"]
        volcano_slug = options["volcano_slug"]

        try:
            organization = Organization.objects.get(slug=organization_slug)
        except Organization.DoesNotExist:
            self.stderr.write(
                f"Organization with slug '{organization_slug}' does not exist."
            )
            return

        try:
            volcano = Volcano.objects.get(slug=volcano_slug)
        except Volcano.DoesNotExist:
            self.stderr.write(f"Volcano with slug '{volcano_slug}' does not exist.")

        run_sinoas(organization, volcano)
