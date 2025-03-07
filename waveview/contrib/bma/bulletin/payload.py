from datetime import datetime

from waveview.event.header import AmplitudeUnit
from waveview.event.models import Amplitude, Event, StationMagnitude
from waveview.inventory.models import Channel


class BulletinPayloadBuilder:
    """
    Build payload from WaveView event object to be sent to BMA bulletin system.
    """

    def __init__(self, event: Event) -> None:
        self.event = event
        self.analog_method = "analog"
        self.digital_method = "bpptkg"

    def _get_amplitude(self) -> str | None:
        amplitude = Amplitude.objects.filter(
            event=self.event, method=self.analog_method
        ).first()
        if amplitude is None:
            return None
        return f"{amplitude.amplitude:.2f}{amplitude.unit}"

    def _get_ml_deles(self) -> float | None:
        try:
            channel = Channel.objects.get_by_stream_id("VG.MEDEL.00.HHZ")
        except Channel.DoesNotExist:
            return None
        amplitude = Amplitude.objects.filter(
            event=self.event, waveform=channel, method=self.digital_method
        ).first()
        if amplitude is None:
            return None
        station_magnitude = StationMagnitude.objects.filter(amplitude=amplitude).first()
        if station_magnitude is None:
            return None
        return station_magnitude.magnitude

    def _get_ml_labuhan(self) -> float | None:
        try:
            channel = Channel.objects.get_by_stream_id("VG.MELAB.00.HHZ")
        except Channel.DoesNotExist:
            return None
        amplitude = Amplitude.objects.filter(
            event=self.event, waveform=channel, method=self.digital_method
        ).first()
        if amplitude is None:
            return None
        station_magnitude = StationMagnitude.objects.filter(amplitude=amplitude).first()
        if station_magnitude is None:
            return None
        return station_magnitude.magnitude

    def _get_ml_pasarbubar(self) -> float | None:
        try:
            channel = Channel.objects.get_by_stream_id("VG.MEPAS.00.HHZ")
        except Channel.DoesNotExist:
            return None
        amplitude = Amplitude.objects.filter(
            event=self.event, waveform=channel, method=self.digital_method
        ).first()
        if amplitude is None:
            return None
        station_magnitude = StationMagnitude.objects.filter(amplitude=amplitude).first()
        if station_magnitude is None:
            return None
        return station_magnitude.magnitude

    def _get_ml_pusunglondon(self) -> float | None:
        try:
            channel = Channel.objects.get_by_stream_id("VG.MEPUS.00.EHZ")
        except Channel.DoesNotExist:
            return None
        amplitude = Amplitude.objects.filter(
            event=self.event, waveform=channel, method=self.digital_method
        ).first()
        if amplitude is None:
            return None
        station_magnitude = StationMagnitude.objects.filter(amplitude=amplitude).first()
        if station_magnitude is None:
            return None
        return station_magnitude.magnitude

    def _get_magnitude(self) -> float | None:
        preferred_magnitude = self.event.preferred_magnitude()
        if preferred_magnitude is not None:
            return preferred_magnitude.magnitude
        return None

    def _get_longitude(self) -> float | None:
        preferred_origin = self.event.preferred_origin()
        if preferred_origin is not None:
            return preferred_origin.longitude
        return None

    def _get_latitude(self) -> float | None:
        preferred_origin = self.event.preferred_origin()
        if preferred_origin is not None:
            return preferred_origin.latitude
        return None

    def _get_depth(self) -> float | None:
        preferred_origin = self.event.preferred_origin()
        if preferred_origin is not None:
            return preferred_origin.depth
        return None

    def _get_seiscompid(self) -> str | None:
        """SeisComP integration is not available yet."""
        return None

    def _format_time(self, time: datetime) -> str:
        return time.isoformat(timespec="seconds")

    def _get_microsecond(self, time: datetime) -> int:
        return int(time.microsecond / 10_000)

    def _get_id(self, event: Event) -> str:
        """
        Get ID of the event. If `refid` is available, use it. Otherwise, use the
        UUID of the event. WaveView uses `refid` to store the ID of the event
        synced from BMA bulletin.
        """
        if event.refid:
            return str(event.refid)
        return str(event.id.hex)

    def build(self) -> dict:
        event = self.event

        eventid: str = self._get_id(event)
        eventdate: str = self._format_time(event.time)
        eventdate_microsecond: int = self._get_microsecond(event.time)
        number: int = 0
        duration: float = event.duration

        amplitude: str = self._get_amplitude()

        magnitude: float = self._get_magnitude()
        longitude: float = self._get_longitude()
        latitude: float = self._get_latitude()
        depth: float = self._get_depth()

        eventtype: str = str(event.type.code)
        seiscompid: str | None = self._get_seiscompid()
        valid: int = 1
        projection: str = "WGS84"
        operator: str = str(event.author.username)
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
