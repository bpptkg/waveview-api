from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.contrib.autopicker.run import run_autopicker


class Command(BaseCommand):
    help = "Run BPPTKG AutoPicker STE/LTE event detection."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        debug = options['debug']
        run_autopicker(debug=debug)
