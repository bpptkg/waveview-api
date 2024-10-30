from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from dateutil import parser
from django.core.management.base import BaseCommand, CommandParser
from django.db import connection

from waveview.contrib.bpptkg.outliers import remove_outliers
from waveview.contrib.bpptkg.response import remove_instrument_response
from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel
from waveview.organization.models import Organization


class Command(BaseCommand):
    help = "Plot filter outlier for certain channel."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("stream_id", type=str, help="Stream ID.")
        parser.add_argument("start", type=str, help="Start time of the query.")
        parser.add_argument("end", type=str, help="End time of the query.")
        parser.add_argument(
            "--remove-response",
            action="store_true",
            help="Remove instrument response.",
        )
        parser.add_argument(
            "--org-slug",
            type=str,
            help="Organization slug.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        start: str = options["start"]
        end: str = options["end"]
        stream_id: str = options["stream_id"]

        try:
            channel = Channel.objects.get_by_stream_id(stream_id)
        except Channel.DoesNotExist:
            self.stderr.write(f"Channel with ID {stream_id} does not exist.")
            return
        channel_id = str(channel.id)

        starttime = parser.parse(start)
        endtime = parser.parse(end)

        datastream = DataStream(connection=connection)
        st = datastream.get_waveform(channel_id, starttime, endtime)
        if len(st) == 0 or len(st[0].data) == 0:
            self.stdout.write(self.style.ERROR("No data found."))
            return

        if options["remove_response"]:
            try:
                organization = Organization.objects.get(slug=options["org_slug"])
            except Organization.DoesNotExist:
                self.stderr.write(
                    f"Organization with slug {options['org_slug']} does not exist."
                )
                return
            st = remove_instrument_response(organization.inventory, st)

        y = st[0].data
        sample_rate = st[0].stats.sampling_rate
        x = np.arange(len(y)) / sample_rate

        w, h = 10, 4
        fig, ax = plt.subplots(figsize=(w, h), nrows=2, sharex=True)
        ax[0].plot(x, y, color="k")
        ax[0].set_ylabel("Original", color="k")

        filtered = remove_outliers(y)
        ax[1].plot(x, filtered, color="k")
        ax[1].set_ylabel("Filtered", color="k")

        ax[0].set_title(stream_id)
        fig.tight_layout()
        fig.savefig(
            "outlier.png",
            format="png",
            transparent=False,
        )
