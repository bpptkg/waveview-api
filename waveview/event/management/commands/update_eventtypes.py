import json
from typing import Any, TypedDict

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from waveview.event.models import EventType
from waveview.organization.models import Organization


class EventTypeDict(TypedDict):
    code: str
    name: str
    description: str
    color: str
    color_light: str
    color_dark: str
    observation_type: str


class Command(BaseCommand):
    help = "Update event types from JSON config file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "path",
            type=str,
            help="Path to the JSON file containing list of event types.",
        )
        parser.add_argument(
            "org",
            type=str,
            help="Organization slug.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        path = options["path"]
        with open(path) as f:
            event_types: list[EventTypeDict] = json.load(f)

        slug = options["org"]
        try:
            organization = Organization.objects.get(slug=slug)
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR("Organization not found."))
            return

        with transaction.atomic():
            for item in event_types:
                code = item.pop("code")
                event_type, created = EventType.objects.update_or_create(
                    organization=organization,
                    code=code,
                    defaults=item,
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created event type {event_type}")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated event type {event_type}")
                    )
