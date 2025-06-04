import logging
from typing import Any

from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from waveview.event.models import Catalog, Event
from waveview.organization.models import Organization
from waveview.tasks.notify_event_observer import OperationType, notify_event_observer
from waveview.volcano.models import Volcano

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Notify observers for events."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--org", type=str, help="Organization slug.")
        parser.add_argument("--volcano", type=str, help="Volcano slug.")
        parser.add_argument("--name", type=str, help="Name of the observer.")
        parser.add_argument(
            "--event-id",
            nargs="*",
            type=str,
            help="ID of the event to calculate magnitudes for.",
        )
        parser.add_argument(
            "--start",
            type=str,
            help="Start date to fetch events (ISO format).",
        )
        parser.add_argument(
            "--end",
            type=str,
            help="End date to fetch events (ISO format).",
        )
        parser.add_argument(
            "--event-type",
            nargs="*",
            type=str,
            help="List of event types to filter events.",
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

        name = options["name"]
        if not name:
            self.stderr.write("Observer name is required.")
            return

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

        event_ids = options["event_id"]
        start = options["start"]
        end = options["end"]
        if event_ids:
            events = Event.objects.filter(
                catalog=catalog,
                id__in=event_ids,
            )
        else:
            if start is not None and end is not None:
                try:
                    start_time = parse(start)
                    if not timezone.is_aware(start_time):
                        start_time = start_time.astimezone(timezone.utc)
                    end_time = parse(end).astimezone(timezone.utc)
                    if not timezone.is_aware(end_time):
                        end_time = end_time.astimezone(timezone.utc)
                except ValueError as e:
                    self.stderr.write(f"Invalid date format: {e}")
                    return

                if start_time >= end_time:
                    self.stderr.write("Start date must be before end date.")
                    return

                events = Event.objects.filter(
                    catalog=catalog,
                    time__gte=start_time,
                    time__lte=end_time,
                )

            else:
                self.stderr.write("Both start and end dates are required for event ID.")
                return

        event_type = options["event_type"]
        if event_type:
            events = events.filter(type__code__in=event_type)

        for index, event in enumerate(events):
            logger.info(
                f"Notifying {name} observer for event {event.id} ({event.type.code}) ({index + 1}/{len(events)})..."
            )
            notify_event_observer(
                OperationType.UPDATE,
                str(event.id),
                str(volcano.id),
                names=name,
            )
