from datetime import timedelta
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
    help = "Plot amplitude for certain channel."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("stream_id", type=str, help="Stream ID.")
        parser.add_argument("start", type=str, help="Start time of the event in UTC.")
        parser.add_argument(
            "duration", type=float, help="Duration of the event in seconds."
        )
        parser.add_argument(
            "--org",
            type=str,
            help="Organization slug. If not provided, will use the first organization.",
        )
        parser.add_argument(
            "--buffer",
            type=int,
            default=0,
            help="Buffer in seconds to add before and after the event.",
        )
        parser.add_argument(
            "--filter-outliers",
            action="store_true",
            help="Remove outliers from the data.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        stream_id: str = options["stream_id"]
        start: str = options["start"]
        duration: float = options["duration"]
        org_slug: str | None = options.get("org")
        buffer: int = options["buffer"]
        filter_outliers: bool = options["filter_outliers"]

        try:
            channel = Channel.objects.get_by_stream_id(stream_id)
        except Channel.DoesNotExist:
            self.stderr.write(f"Channel with ID {stream_id} does not exist.")
            return
        channel_id = str(channel.id)

        starttime = parser.parse(start)
        starttime = starttime - timedelta(seconds=buffer)
        endtime = starttime + timedelta(seconds=duration + 2 * buffer)

        datastream = DataStream(connection=connection)
        st = datastream.get_waveform(channel_id, starttime, endtime)
        self.stdout.write(f"{st} | minmax: {min(st[0].data)}, {max(st[0].data)}")
        if len(st) == 0 or len(st[0].data) == 0:
            self.stdout.write(self.style.ERROR("No data found."))
            return

        st_copy = st.copy()
        raw = st_copy[0].data
        sample_rate = st_copy[0].stats.sampling_rate
        ts = np.arange(len(raw)) / sample_rate

        w, h = 10, 4
        fig, ax = plt.subplots(figsize=(w, h), nrows=2, sharex=True)
        ax[0].plot(ts, raw, color="k")
        ax[0].set_ylabel("Original", color="k")

        try:
            if org_slug is None:
                organization = Organization.objects.first()
            else:
                organization = Organization.objects.get(slug=org_slug)
        except Organization.DoesNotExist:
            self.stderr.write(
                f"Organization with slug {options['org_slug']} does not exist."
            )
            return

        st = remove_instrument_response(organization.inventory, st)
        if filter_outliers:
            data = remove_outliers(st[0].data)
        else:
            data = st[0].data

        if len(data) == 0:
            amax = 0
        else:
            minval = np.min(data)
            maxval = np.max(data)
            amax = (maxval - minval) / 2
        self.stdout.write(self.style.SUCCESS(f"Amplitude: {amax*1e6} um"))

        ax[1].plot(ts, data, color="k")
        ax[1].set_ylabel("Response Removed", color="k")

        ax[0].set_title(stream_id)
        fig.tight_layout()
        fig.savefig(
            "amplitude.png",
            format="png",
            transparent=False,
        )
