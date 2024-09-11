import json
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.seeds.hypocenter import HypocenterDataSeeder, HypocenterDataSeederOptions


class Command(BaseCommand):
    help = "Generate dummy event and hypocenter data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=str, help="Path to the JSON config file.")

    def handle(self, *args: Any, **options: Any) -> None:
        path = options["path"]
        with open(path) as f:
            config = json.load(f)

        options = HypocenterDataSeederOptions.from_dict(config)
        seeder = HypocenterDataSeeder()
        seeder.run(options)
