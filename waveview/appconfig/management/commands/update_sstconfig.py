import json
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.appconfig.models import SeismogramStationConfig
from waveview.inventory.models import Station


class Command(BaseCommand):
    help = "Update seismogram station configuration."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=str, help="Path to the JSON config file.")
        parser.add_argument("seismogram_config", type=str, help="Seismogram config ID.")

    def handle(self, *args: Any, **options: Any) -> None:
        path = options["path"]
        seismogram_config = options["seismogram_config"]
        with open(path) as f:
            items = json.load(f)

        for item in items:
            try:
                station = Station.objects.get(code=item["station"])
            except Station.DoesNotExist:
                self.stdout.write(f"Station {item['station']} not found.")
                continue
            SeismogramStationConfig.objects.update_or_create(
                seismogram_config_id=seismogram_config,
                station=station,
                defaults={
                    "color": item.get("color"),
                    "color_light": item.get("color_light"),
                    "color_dark": item.get("color_dark"),
                    "order": item.get("order", 0),
                },
            )
            self.stdout.write(f"Updated station {item['station']}.")
