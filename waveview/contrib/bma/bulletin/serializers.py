from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class BulletinPayloadSerializer(serializers.Serializer):
    eventid = serializers.CharField(help_text=_("Event ID."))
    eventdate = serializers.DateTimeField(help_text=_("Event date."))
    eventdate_microsecond = serializers.IntegerField(
        help_text=_("Event microseconds."), allow_null=True
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
