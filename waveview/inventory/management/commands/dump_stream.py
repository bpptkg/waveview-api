from typing import Any

from dateutil.parser import parse
from django.core.management.base import BaseCommand, CommandParser
from django.db import connection

from waveview.inventory.datastream import DataStream
from waveview.inventory.models import Channel


class Command(BaseCommand):
    help = "Dump stream from the database to msd file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "stream_id", type=str, help="Stream ID, e.g. 'IU.ANMO.00.BHZ'."
        )
        parser.add_argument("start", type=str, help="Start time in UTC.")
        parser.add_argument("end", type=str, help="End time in UTC.")

    def handle(self, *args: Any, **options: Any) -> None:
        stream_id: str = options["stream_id"]
        start: str = options["start"]
        end: str = options["end"]
        sid = stream_id.split(".")
        if len(sid) != 4:
            self.stderr.write(self.style.ERROR("Invalid stream ID."))
            return

        network, station, __, channel = sid
        chan = Channel.objects.filter(
            code=channel, station__code=station, station__network__code=network
        ).first()
        if not chan:
            self.stderr.write(self.style.ERROR("Channel not found."))
            return

        datastream = DataStream(connection)
        starttime = parse(start)
        endtime = parse(end)
        self.stdout.write(
            f"Dumping stream {stream_id} from {starttime} to {endtime}..."
        )
        st = datastream.get_waveform(chan.id, starttime, endtime)
        self.stdout.write(str(st))
        datefmt = "%Y%m%dT%H%M%S"
        st.write(
            f"{stream_id}_{starttime.strftime(datefmt)}_{endtime.strftime(datefmt)}.msd",
            format="MSEED",
        )
        self.stdout.write("Done.")
