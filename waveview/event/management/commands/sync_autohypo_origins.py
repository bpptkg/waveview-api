import logging
from typing import Any

from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from waveview.contrib.bma.bulletin.autohypo import sync_autohypo
from waveview.event.models import Catalog
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Copy BMA autohypo locations onto verified VEPS events."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--org", type=str, help="Organization slug.")
        parser.add_argument("--volcano", type=str, help="Volcano slug.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print matches without writing origins.",
        )
        parser.add_argument("--start", type=str, help="Window start.")
        parser.add_argument("--end", type=str, help="Window end.")
        parser.add_argument(
            "--hours",
            type=int,
            help="Hours before the end time. Overrides --start.",
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

        end = options["end"]
        if end is None:
            end = timezone.now()
        else:
            end = parse(end)
            if not timezone.is_aware(end):
                end = timezone.make_aware(end)

        start = options["start"]
        if start is None:
            start = end - timezone.timedelta(days=1)
        else:
            start = parse(start)
            if not timezone.is_aware(start):
                start = timezone.make_aware(start)

        hours = options["hours"]
        if hours:
            start = end - timezone.timedelta(hours=hours)

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
            catalog = Catalog.objects.get(volcano=volcano, is_default=True)
        except Catalog.DoesNotExist:
            self.stderr.write(
                f"Default catalog for volcano '{volcano.name}' does not exist."
            )
            return

        logger.info(
            "Copying autohypo origins for %s (%s) from %s to %s",
            organization,
            volcano,
            start,
            end,
        )
        sync_autohypo(catalog, start, end, dry_run=options["dry_run"])
        logger.info("Done.")
