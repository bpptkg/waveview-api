import json
from typing import Any, TypedDict

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from waveview.observation.models import FallDirection
from waveview.volcano.models import Volcano


class FallDirectionDict(TypedDict):
    name: str
    azimuth: float


class Command(BaseCommand):
    help = "Update fall directions from JSON config file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "path",
            type=str,
            help="Path to the JSON file containing list of fall directions.",
        )
        parser.add_argument(
            "volcano",
            type=str,
            help="Volcano slug.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        path = options["path"]
        with open(path) as f:
            items: list[FallDirectionDict] = json.load(f)

        slug = options["volcano"]
        try:
            volcano = Volcano.objects.get(slug=slug)
        except Volcano.DoesNotExist:
            self.stdout.write(self.style.ERROR("Volcano not found."))
            return

        with transaction.atomic():
            for item in items:
                name = item["name"]
                azimuth = item["azimuth"]
                fall_direction, created = FallDirection.objects.update_or_create(
                    volcano=volcano, name=name, defaults={"azimuth": azimuth}
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created fall direction {fall_direction}")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated fall direction {fall_direction}")
                    )
