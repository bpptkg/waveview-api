import logging
from typing import Any

from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from waveview.appconfig.models import EventObserverConfig
from waveview.contrib.bma.bulletin.client import BulletinClient
from waveview.contrib.bma.bulletin.sync import (
    BulletinSynchronizer,
    BulletinSynchronizerContext,
)
from waveview.contrib.bma.bulletin.types import BulletinData
from waveview.event.models import Catalog
from waveview.organization.models import Organization
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync WaveView catalog to BMA bulletin."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--org", type=str, help="Organization slug.")
        parser.add_argument("--volcano", type=str, help="Volcano slug.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Dry run mode. Do not create events, only print the fetched events.",
        )
        parser.add_argument(
            "--start",
            type=str,
            help="Start date to fetch the events.",
        )
        parser.add_argument(
            "--end",
            type=str,
            help="End date to fetch the events.",
        )
        parser.add_argument(
            "--event-id",
            type=str,
            help="Run for certain Event ID only.",
        )
        parser.add_argument(
            "--hours",
            type=int,
            help="Number of hours since now to fetch events.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        first = parse("2024-11-18T05:00:00Z")

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

        dry_run = options["dry_run"]
        event_id = options["event_id"]
        hours = options["hours"]
        if hours:
            start = end - timezone.timedelta(hours=hours)
        if start < first:
            start = first

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

        try:
            config = EventObserverConfig.objects.get(name="bma.bulletin")
        except EventObserverConfig.DoesNotExist:
            self.stderr.write("Event observer config 'bma.bulletin' does not exist.")
            return

        logger.info(
            f"Syncing BMA bulletin events for {organization} ({volcano}) from {start} to {end}..."
        )

        data = BulletinData.from_dict(config.data)
        client = BulletinClient(data.server_url, data.token)
        context = BulletinSynchronizerContext(
            client=client,
            organization=organization,
            volcano=volcano,
            catalog=catalog,
        )
        synchronizer = BulletinSynchronizer(context)
        if event_id:
            synchronizer.sync_by_id(event_id, dry_run=dry_run)
        else:
            synchronizer.sync_in_range(start, end, dry_run=dry_run)

        logger.info("Done.")
