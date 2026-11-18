from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.contrib.autopicker.run_multi import run_autopicker_multi


class Command(BaseCommand):
    help = (
        "Run BPPTKG AutoPicker dengan detektor voting multi-stasiun. "
        "Bawaan: mode shadow (hanya mencatat ke CSV, tidak membuat event di basis data)."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
        parser.add_argument(
            "--live",
            action="store_true",
            help="Buat event di basis data (create_event). Tanpa opsi ini hanya mencatat ke CSV.",
        )
        parser.add_argument(
            "--log-dir",
            default=None,
            help="Folder log CSV (bawaan: $AUTOPICKER_MULTI_LOG_DIR atau ./autopicker_multi_logs).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        run_autopicker_multi(
            debug=options["debug"],
            shadow=not options["live"],
            log_dir=options["log_dir"],
        )
