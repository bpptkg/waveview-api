from typing import Any

from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from waveview.contrib.bma.bulletin.loader import BulletinLoader, BulletinLoaderContext
from waveview.event.models import Catalog
from waveview.organization.models import Organization
from waveview.users.models import User
from waveview.volcano.models import Volcano


class Command(BaseCommand):
    help = "Load BMA events and create events in the system."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--org", type=str, help="Organization slug.")
        parser.add_argument("--volcano", type=str, help="Volcano slug.")
        parser.add_argument("--user", type=str, help="User who triggered the event.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode. Do not create events, only print the fetched events.",
        )
        parser.add_argument(
            "--start",
            type=str,
            help="Start date to fetch BMA bulletins.",
        )
        parser.add_argument(
            "--end",
            type=str,
            help="End date to fetch BMA bulletins.",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean unsynched events for particular time range.",
        )
        parser.add_argument(
            "--skip-update-amplitudes",
            action="store_true",
            help="Skip update amplitudes for existing events.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        org_slug = options["org"]
        if not org_slug:
            self.stderr.write("Organization slug is required.")
            return
        volcano_slug = options["volcano"]
        if not volcano_slug:
            self.stderr.write("Volcano slug is required.")
            return

        user = options["user"]
        if not user:
            self.stderr.write("User is required.")
            return
        end = options["end"]
        if end is None:
            end = timezone.now()
        else:
            end = parse(end)
            end = timezone.make_aware(end)
        start = options["start"]
        if start is None:
            start = end - timezone.timedelta(days=7)
        else:
            start = parse(start)
            start = timezone.make_aware(start)
        dry_run = options["dry_run"]
        clean = options["clean"]
        skip_update_amplitudes = options["skip_update_amplitudes"]

        try:
            organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            self.stderr.write(f"Organization with slug '{org_slug}' does not exist.")
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

        try:
            catalog = Catalog.objects.get(volcano=volcano, is_default=True)
        except Catalog.DoesNotExist:
            self.stderr.write(
                f"Default catalog for volcano '{volcano.name}' does not exist."
            )
            return

        context = BulletinLoaderContext(
            organization=organization,
            volcano=volcano,
            catalog=catalog,
            user=user,
        )
        loader = BulletinLoader(context)
        loader.load(
            start=start,
            end=end,
            clean=clean,
            skip_update_amplitudes=skip_update_amplitudes,
            dry_run=dry_run,
        )
