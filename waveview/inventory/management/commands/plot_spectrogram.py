from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from dateutil import parser
from django.core.management.base import BaseCommand, CommandParser
from django.db import connection
from rest_framework import serializers

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel
from waveview.signal.spectrogram import get_cmap, spectrogram


class Command(BaseCommand):
    help = "Plot spectrogram for certain channel."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("stream_id", type=str, help="Stream ID.")
        parser.add_argument("start", type=str, help="Start time of the spectrogram.")
        parser.add_argument("end", type=str, help="End time of the spectrogram.")

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

        data = st[0].data
        sample_rate = st[0].stats.sampling_rate
        specgram, time, freq, norm = spectrogram(data, sample_rate, freqmax=25)

        cmap = get_cmap()
        w, h = 10, 4
        fig, ax1 = plt.subplots(figsize=(w, h))
        ax1.imshow(
            specgram,
            aspect="auto",
            norm=norm,
            origin="lower",
            extent=[time.min(), time.max(), freq.min(), freq.max()],
            cmap=cmap,
        )
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Frequency (Hz)")

        ax2 = ax1.twinx()
        time_signal = np.arange(len(data)) / sample_rate
        ax2.plot(time_signal, data, color="k")
        ax2.set_ylabel("Amplitude", color="k")
        ax2.tick_params(axis="y", labelcolor="k")

        fig.tight_layout(pad=0)
        fig.savefig(
            "spectrogram.png",
            format="png",
            transparent=False,
            bbox_inches="tight",
            pad_inches=0,
        )
