import re
from typing import Any


class StreamIdentifier:
    """
    A class to store stream identifier.

    A stream identifier refer to a specific waveform data to which RSAM/SSAM
    value is calculated. It also used as running context identifier where each
    stream can be run in parallel or asynchronous manner.
    """

    def __init__(
        self,
        id: str | None = None,
        network: str | None = None,
        station: str | None = None,
        location: str | None = None,
        channel: str | None = None,
    ) -> None:
        if id:
            values = self.parse(id)
            self.network = values["network"]
            self.station = values["station"]
            self.location = values["location"]
            self.channel = values["channel"]
        else:
            self.network = network
            self.station = station
            self.location = location
            self.channel = channel

    @staticmethod
    def parse(id: str) -> dict[str, str]:
        pattern = re.compile(
            r"""
            (?P<network>\w+)\.
            (?P<station>\w+)\.
            (?P<location>\d*)\.
            (?P<channel>\w+)
        """,
            re.X,
        )
        match = pattern.match(id)
        if match is not None:
            return match.groupdict()
        else:
            msg = "Stream identifier {} is not valid.".format(id)
            raise ValueError(msg)

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return "<{}: {}>".format(self.__class__.__name__, self.id)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.id == other
        elif isinstance(other, StreamIdentifier):
            return (
                self.network == other.network
                and self.station == other.station
                and self.location == other.location
                and self.channel == other.channel
            )
        return False

    @property
    def id(self) -> str:
        return "{network}.{station}.{location}.{channel}".format(
            network=self.network,
            station=self.station,
            location=self.location,
            channel=self.channel,
        )

    @id.deleter
    def id(self) -> None:
        msg = "Identifier value cannot be deleted."
        raise ValueError(msg)
