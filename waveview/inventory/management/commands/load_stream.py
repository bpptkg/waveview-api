import io
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import connection
from obspy import Trace, read

from waveview.inventory.db.schema import TimescaleSchemaEditor
from waveview.inventory.models import Channel
from waveview.inventory.datastream import preparebuffer


class Command(BaseCommand):
    help = "Load stream file to the database."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=str, help="Path to the stream file.")
        parser.add_argument(
            "--stream_id", type=str, help="Stream ID, e.g. 'IU.ANMO.00.BHZ'."
        )
        parser.add_argument(
            "--reclen", type=int, default=512, help="MiniSeed record length."
        )
        parser.add_argument(
            "--chunksize",
            type=int,
            default=1,
            help="Chunksize in multiples of the record length.",
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

        reclen: int = options["reclen"]
        chunksize: int = options["chunksize"]
        size = reclen * chunksize
        schema = TimescaleSchemaEditor(connection)

        nbytes = 0
        compressed = 0
        with io.open(path, "rb") as f:
            while True:
                with io.BytesIO() as chunk:
                    c = f.read(size)
                    if not c:
                        break
                    chunk.write(c)
                    chunk.seek(0, 0)
                    stream = read(chunk)

                for trace in stream:
                    trace: Trace
                    st, et, sr, dtype, buf = preparebuffer(trace)
                    schema.insert(table, st, et, sr, dtype, buf)

                    nbytes += trace.data.nbytes
                    compressed += len(buf)

                    if print_info:
                        self.stdout.write(trace)

        self.stdout.write(
            "Data loaded: {:,} bytes, compressed: {:,} bytes.".format(
                nbytes, compressed
            )
        )
        compression_ratio = (compressed / nbytes) * 100
        self.stdout.write(f"Compression ratio: {compression_ratio:.2f}%")
