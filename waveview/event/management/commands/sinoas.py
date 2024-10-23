from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.contrib.sinoas.adapter import run_sinoas
from waveview.organization.models import Organization
from waveview.users.models import User
from waveview.volcano.models import Volcano


class Command(BaseCommand):
    help = "Run the SINOAS event detection."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("organization_slug", type=str, help="Organization slug.")
        parser.add_argument("volcano_slug", type=str, help="Volcano slug.")
        parser.add_argument("user", type=str, help="User who triggered the event.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode. Do not create events.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        organization_slug = options["organization_slug"]
        volcano_slug = options["volcano_slug"]
        user = options["user"]
        dry_run = options["dry_run"]

        try:
            organization = Organization.objects.get(slug=organization_slug)
        except Organization.DoesNotExist:
            self.stderr.write(
                f"Organization with slug '{organization_slug}' does not exist."
            )
            return

        try:
            volcano = Volcano.objects.get(organization=organization, slug=volcano_slug)
        except Volcano.DoesNotExist:
            self.stderr.write(f"Volcano with slug '{volcano_slug}' does not exist.")
            return

        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            self.stderr.write(f"User with username '{user}' does not exist.")
            return

        run_sinoas(organization, volcano, user)
