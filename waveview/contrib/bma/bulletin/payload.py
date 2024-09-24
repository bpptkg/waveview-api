from datetime import datetime

from waveview.event.models import Event, StationMagnitude, Amplitude
from waveview.inventory.models import Channel


class BulletinPayloadBuilder:
    def __init__(self, event: Event) -> None:
        self.event = event

    def _get_amplitude(self) -> str:
        return "0mm"

    def _get_ml_deles(self) -> float | None:
        return 0

    def _get_ml_labuhan(self) -> float | None:
        return 0

    def _get_ml_pasarbubar(self) -> float | None:
        return 0

    def _get_ml_pusunglondon(self) -> float | None:
        return 0

    def _get_magnitude(self) -> float:
        return 0

    def _get_longitude(self) -> float:
        return 0

    def _get_latitude(self) -> float:
        return 0

    def _get_depth(self) -> float:
        return 0

    def _get_seiscompid(self) -> str | None:
        return None

    def _format_time(self, time: datetime) -> str:
        return time.isoformat(timespec="seconds")

    def _get_microsecond(self, time: datetime) -> int:
        return int(time.microsecond / 10_000)

    def build(self) -> dict:
        event = self.event

        eventid: str = str(event.id)
        eventdate: str = self._format_time(event.time)
        eventdate_microsecond: int = self._get_microsecond(event.time)
        number: int = 0
        duration: float = event.duration

        amplitude: str = self._get_amplitude()

        magnitude: float = self._get_magnitude()
        longitude: float = self._get_longitude()
        latitude: float = self._get_latitude()
        depth: float = self._get_depth()

        eventtype: str = event.type.code
        seiscompid: str | None = self._get_seiscompid()
        valid: int = 1
        projection: str = "WGS84"
        operator: str = event.author.username
        timestamp: str = self._format_time(event.updated_at)
        timestamp_microsecond: int = self._get_microsecond(event.updated_at)
        count_deles: int = 0
        count_labuhan: int = 0
        count_pasarbubar: int = 0
        count_pusunglondon: int = 0
        ml_deles: float | None = self._get_ml_deles()
        ml_labuhan: float | None = self._get_ml_labuhan()
        ml_pasarbubar: float | None = self._get_ml_pasarbubar()
        ml_pusunglondon: float | None = self._get_ml_pusunglondon()
        location_mode: str = "automatic"
        location_type: str = "earthquake"

        return {
            "eventid": eventid,
            "eventdate": eventdate,
            "eventdate_microsecond": eventdate_microsecond,
            "number": number,
            "duration": duration,
            "amplitude": amplitude,
            "magnitude": magnitude,
            "longitude": longitude,
            "latitude": latitude,
            "depth": depth,
            "eventtype": eventtype,
            "seiscompid": seiscompid,
            "valid": valid,
            "projection": projection,
            "operator": operator,
            "timestamp": timestamp,
            "timestamp_microsecond": timestamp_microsecond,
            "count_deles": count_deles,
            "count_labuhan": count_labuhan,
            "count_pasarbubar": count_pasarbubar,
            "count_pusunglondon": count_pusunglondon,
            "ml_deles": ml_deles,
            "ml_labuhan": ml_labuhan,
            "ml_pasarbubar": ml_pasarbubar,
            "ml_pusunglondon": ml_pusunglondon,
            "location_mode": location_mode,
            "location_type": location_type,
        }
