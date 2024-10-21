import logging
from dataclasses import dataclass
from datetime import datetime

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.header import (
    AmplitudeCategory,
    AmplitudeUnit,
    EvaluationMode,
    EvaluationStatus,
    MagnitudeType,
)
from waveview.event.models import Amplitude, Event, EventType, Magnitude, Origin
from waveview.inventory.models import Channel, Station

logger = logging.getLogger(__name__)


@dataclass
class ChannelItem:
    stream_id: str
    ml: float | None


def parse_amplitude(value: str) -> float:
    """
    Parse amplitude value from string to float.

    The amplitude value is in mm format. The value is converted to float
    by removing the 'mm' suffix.
    """
    try:
        return float(value.lower().strip().replace("mm", ""))
    except ValueError:
        return 0.0


class BulletinPayloadSerializer(serializers.Serializer):
    eventid = serializers.CharField(help_text=_("Event ID."))
    eventdate = serializers.DateTimeField(help_text=_("Event date."))
    eventdate_microsecond = serializers.IntegerField(
        help_text=_("Event microseconds."), allow_null=True, default=0
    )
    number = serializers.IntegerField(help_text=_("Event number."), allow_null=True)
    duration = serializers.FloatField(
        help_text=_("Event duration in seconds."), allow_null=True
    )
    amplitude = serializers.CharField(
        help_text=_("Event amplitude in mm."), allow_null=True
    )
    magnitude = serializers.FloatField(help_text=_("Event magnitude."), allow_null=True)
    longitude = serializers.FloatField(
        help_text=_("Event longitude in degrees."), allow_null=True
    )
    latitude = serializers.FloatField(
        help_text=_("Event latitude in degrees."), allow_null=True
    )
    depth = serializers.FloatField(help_text=_("Event depth in km."), allow_null=True)
    eventtype = serializers.CharField(help_text=_("Event type."), allow_null=True)
    seiscompid = serializers.CharField(help_text=_("Seiscomp ID."), allow_null=True)
    valid = serializers.IntegerField(help_text=_("Validation status."), allow_null=True)
    projection = serializers.CharField(
        help_text=_("Geodetic projection."), allow_null=True
    )
    operator = serializers.CharField(help_text=_("Operator ID."), allow_null=True)
    timestamp = serializers.DateTimeField(
        help_text=_("Last modified date."), allow_null=True
    )
    timestamp_microsecond = serializers.IntegerField(
        help_text=_("Last modified microseconds."), allow_null=True
    )
    count_deles = serializers.IntegerField(help_text=_("Count Deles."), allow_null=True)
    count_labuhan = serializers.IntegerField(
        help_text=_("Count Labuhan."), allow_null=True
    )
    count_pasarbubar = serializers.IntegerField(
        help_text=_("Count Pasarbubar."), allow_null=True
    )
    count_pusunglondon = serializers.IntegerField(
        help_text=_("Count Pusunglondon."), allow_null=True
    )
    ml_deles = serializers.FloatField(help_text=_("ML Deles."), allow_null=True)
    ml_labuhan = serializers.FloatField(help_text=_("ML Labuhan."), allow_null=True)
    ml_pasarbubar = serializers.FloatField(
        help_text=_("ML Pasarbubar."), allow_null=True
    )
    ml_pusunglondon = serializers.FloatField(
        help_text=_("ML Pusunglondon."), allow_null=True
    )
    location_mode = serializers.CharField(
        help_text=_("Location mode."), allow_null=True
    )
    location_type = serializers.CharField(
        help_text=_("Location type."), allow_null=True
    )

    def validate_duration(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_amplitude(self, value: str | None) -> str:
        if value is None:
            return "0mm"
        return value

    def validate_magnitude(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_longitude(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_latitude(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_depth(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_eventtype(self, value: str | None) -> str:
        if value is None:
            return "UNKNOWN"
        return value

    def validate_seiscompid(self, value: str | None) -> str:
        if value is None:
            return "0"
        return value

    def validate_operator(self, value: str | None) -> str:
        if value is None:
            return ""
        return value

    def validate_ml_deles(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_ml_labuhan(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_ml_pasarbubar(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_ml_pusunglondon(self, value: float | None) -> float:
        if value is None:
            return 0
        return value

    def validate_location_mode(self, value: str | None) -> str:
        if value is None:
            return "not_defined"
        return value

    def validate_location_type(self, value: str | None) -> str:
        if value is None:
            return "not_defined"
        return value

    @transaction.atomic
    def create(self, validated_data: dict) -> Event:
        catalog_id = self.context["catalog_id"]
        user = self.context["request"].user

        eventid = validated_data["eventid"]
        eventdate = validated_data["eventdate"]
        duration = validated_data.get("duration", 0)
        amplitude = validated_data.get("amplitude", "0mm")
        magnitude = validated_data.get("magnitude", 0)
        longitude = validated_data.get("longitude", 0)
        latitude = validated_data.get("latitude", 0)
        depth = validated_data.get("depth", 0)
        eventtype = validated_data.get("eventtype", "UNKNOWN")
        seiscompid = validated_data.get("seiscompid", "0")
        operator = validated_data.get("operator", "")
        ml_deles = validated_data.get("ml_deles", 0)
        ml_labuhan = validated_data.get("ml_labuhan", 0)
        ml_pasarbubar = validated_data.get("ml_pasarbubar", 0)
        ml_pusunglondon = validated_data.get("ml_pusunglondon", 0)
        location_mode = validated_data.get("location_mode", "not_defined")
        location_type = validated_data.get("location_type", "not_defined")

        time: datetime = eventdate
        if not duration:
            duration = 30
        try:
            event_type = EventType.objects.get(code=eventtype)
            type_id = event_type.id
        except EventType.DoesNotExist:
            try:
                event_type = EventType.objects.get(code="UNKNOWN")
                type_id = event_type.id
            except EventType.DoesNotExist:
                type_id = None

        try:
            sof: Station = Station.objects.filter(code="MEPSL").get()
            station_of_first_arrival_id = str(sof.id)
        except Channel.DoesNotExist:
            station_of_first_arrival_id = None

        method = "webobs"
        if eventtype == "AUTO":
            evaluation_mode = EvaluationMode.AUTOMATIC
            evaluation_status = EvaluationStatus.PRELIMINARY
        else:
            evaluation_mode = EvaluationMode.MANUAL
            evaluation_status = EvaluationStatus.CONFIRMED
        note = (
            f"Synched from BMA.\n"
            f"Event ID: {eventid}\n"
            f"Seiscomp ID: {seiscompid}\n"
            f"Operator: {operator}\n"
            f"Location Mode: {location_mode}\n"
            f"Location Type: {location_type}"
        )
        event, created = Event.objects.update_or_create(
            catalog_id=catalog_id,
            refid=eventid,
            defaults=dict(
                station_of_first_arrival_id=station_of_first_arrival_id,
                time=time,
                duration=duration,
                type_id=type_id,
                note=note,
                method=method,
                evaluation_mode=evaluation_mode,
                evaluation_status=evaluation_status,
                author=user,
            ),
        )
        if created:
            logger.info(f"Event {eventid} successfully created.")
        else:
            logger.info(f"Event {eventid} successfully updated.")

        Magnitude.objects.update_or_create(
            event=event,
            method="webobs",
            type=MagnitudeType.ML,
            defaults=dict(
                magnitude=magnitude,
                station_count=0,
                azimuthal_gap=0,
                evaluation_status=EvaluationStatus.PRELIMINARY,
                is_preferred=False,
            ),
        )

        try:
            amplitude_channel: Channel = Channel.objects.get_by_stream_id(
                "VG.MEPUS.EHZ"
            )
        except Channel.DoesNotExist:
            amplitude_channel = None

        Amplitude.objects.update_or_create(
            event=event,
            method="webobs",
            defaults=dict(
                amplitude=parse_amplitude(amplitude),
                type="Amax",
                category=AmplitudeCategory.OTHER,
                time=time,
                begin=0,
                end=duration,
                snr=0,
                unit=AmplitudeUnit.MM,
                waveform=amplitude_channel,
                evaluation_mode=EvaluationMode.MANUAL,
                author=user,
                is_preferred=False,
            ),
        )

        channel_items: list[ChannelItem] = [
            ChannelItem("VG.MEDEL.HHZ", ml_deles),
            ChannelItem("VG.MELAB.HHZ", ml_labuhan),
            ChannelItem("VG.MEPAS.HHZ", ml_pasarbubar),
            ChannelItem("VG.MEPUS.EHZ", ml_pusunglondon),
        ]
        for item in channel_items:
            if item.ml is None:
                ml = 0
            else:
                ml = item.ml
            Magnitude.objects.update_or_create(
                event=event,
                method="bpptkg",
                type="ML_" + item.stream_id,
                defaults=dict(
                    magnitude=ml,
                    station_count=1,
                    azimuthal_gap=0,
                    evaluation_status=EvaluationStatus.PRELIMINARY,
                    is_preferred=False,
                ),
            )

        Origin.objects.update_or_create(
            event=event,
            defaults=dict(
                time=time,
                latitude=latitude,
                latitude_uncertainty=0,
                longitude=longitude,
                longitude_uncertainty=0,
                depth=depth,
                depth_uncertainty=0,
                method="webobs",
                earth_model="merapi",
                evaluation_mode=EvaluationMode.MANUAL,
                evaluation_status=EvaluationStatus.CONFIRMED,
                is_preferred=True,
                author=user,
            ),
        )

        return event

    def update(self, instance: Event, validated_data: dict) -> Event:
        raise NotImplementedError("Update is not implemented.")
