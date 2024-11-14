from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import connection
from obspy import Trace, read

from waveview.inventory.datastream import prepare_buffer
from waveview.inventory.db.schema import TimescaleSchemaEditor
from waveview.inventory.models import Channel


class Command(BaseCommand):
    help = "Load stream file to the database."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=str, help="Path to the stream file.")
        parser.add_argument(
            "--stream_id", type=str, help="Stream ID, e.g. 'IU.ANMO.00.BHZ'."
        )
        parser.add_argument(
            "--chunksize",
            type=int,
            default=4,
            help="Chunksize of the window in seconds.",
        )
        parser.add_argument(
            "--print-info", action="store_true", help="Print trace information."
        )
        parser.add_argument("--table", type=str, help="Table name to store the data.")

    def handle(self, *args: Any, **options: Any) -> None:
        path: str = options["path"]
        if not Path(path).exists():
            self.stderr.write(self.style.ERROR("File not found."))
            return

        print_info: bool = options["print_info"]
        stream_id: str = options.get("stream_id", "")
        table_name: str = options.get("table", "")
        if table_name:
            table = table_name
        elif stream_id:
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

            table = chan.get_datastream_id()
        else:
            self.stderr.write(self.style.ERROR("Stream ID or table name is missing."))
            return

        schema = TimescaleSchemaEditor(connection)
        chunksize = options["chunksize"]
        nbytes: int = 0
        compressed: int = 0

        st = read(path, format="mseed")
        for trace in st:
            trace: Trace
            starttime = trace.stats.starttime
            endtime = trace.stats.endtime

            while starttime < endtime:
                chunk_start = starttime
                chunk_end = starttime + chunksize
                if chunk_end > endtime:
                    chunk_end = endtime

                chunk = trace.slice(chunk_start, chunk_end)
                st, et, sr, dtype, buf = prepare_buffer(chunk)
                schema.insert(table, st, et, sr, dtype, buf)

                nbytes += chunk.data.nbytes
                compressed += len(buf)

                if print_info:
                    self.stdout.write(trace)

                starttime = chunk_end

        self.stdout.write(
            "Data loaded: {:,} bytes, compressed: {:,} bytes.".format(
                nbytes, compressed
            )
        )
        compression_ratio = (compressed / nbytes) * 100
        self.stdout.write(f"Compression ratio: {compression_ratio:.2f}%")
