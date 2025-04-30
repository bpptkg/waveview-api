from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from waveview.tasks.notify_new_version import notify_new_version


class Command(BaseCommand):
    help = "Notify new version of the app to the organization."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "version",
            type=str,
            help="Version of the app to notify.",
        )
        parser.add_argument(
            "--no-reload",
            action="store_true",
            help="Whether to reload the app after notifying.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=-1,
            help="Timeout for the notification.",
        )
        parser.add_argument(
            "--reload-timeout",
            type=int,
            default=30,
            help="Timeout for the reload.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        version = options["version"]
        reload = not options["no_reload"]
        timeout = options["timeout"]
        reload_timeout = options["reload_timeout"]
        notify_new_version.delay(version, reload, timeout, reload_timeout)
        self.stdout.write(self.style.SUCCESS(f"Notified new version: {version}"))
