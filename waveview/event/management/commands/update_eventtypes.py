import json
from typing import Any, TypedDict

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from waveview.event.models import EventType
from waveview.organization.models import Organization


class EventTypeDict(TypedDict):
    code: str
    name: str
    color: str
    color_light: str
    color_dark: str


class Command(BaseCommand):
    help = "Update event types from JSON config file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "path",
            type=str,
            help="Path to the JSON file containing list of event types.",
        )
        parser.add_argument(
            "organization_id",
            type=str,
            help="Organization ID to update event types for. Use 'first' to update the first organization.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        path = options["path"]
        with open(path) as f:
            event_types: list[EventTypeDict] = json.load(f)

        organization_id = options["organization_id"]
        try:
            if organization_id == "first":
                organization = Organization.objects.first()
            else:
                organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            self.stdout.write(self.style.ERROR("Organization not found."))
            return

        with transaction.atomic():
            for item in event_types:
                code = item["code"]
                name = item["name"]
                color = item["color"]
                color_light = item["color_light"]
                color_dark = item["color_dark"]

                event_type, created = EventType.objects.update_or_create(
                    organization=organization,
                    code=code,
                    defaults={
                        "name": name,
                        "color": color,
                        "color_light": color_light,
                        "color_dark": color_dark,
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created event type {event_type}")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated event type {event_type}")
                    )
