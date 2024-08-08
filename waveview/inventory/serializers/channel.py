from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.inventory.header import RestrictedStatus
from waveview.inventory.models import Channel


class ChannelSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Channel ID."))
    station_id = serializers.UUIDField(help_text=_("Station ID."))
    code = serializers.CharField(help_text=_("Channel code."))
    alternate_code = serializers.CharField(
        help_text=_("Alternate code used for display or association."), allow_null=True
    )
    start_date = serializers.DateTimeField(
        help_text=_("Start date of channel."), allow_null=True
    )
    end_date = serializers.DateTimeField(
        help_text=_("End date of channel."), allow_null=True
    )
    historical_code = serializers.CharField(
        help_text=_("Historical code of channel."), allow_null=True
    )
    location_code = serializers.CharField(
        help_text=_("Location code of channel."), allow_null=True
    )
    latitude = serializers.FloatField(
        help_text=_(
            """
            Latitude of this channel’s sensor, in degrees. Often the same as the
            station latitude, but when different the channel latitude is the true
            location of the sensor.
            """
        ),
        allow_null=True,
    )
    longitude = serializers.FloatField(
        help_text=_(
            """
            Longitude of this channel’s sensor, in degrees. Often the same as the
            station longitude, but when different the channel longitude is the true
            location of the sensor.
            """
        ),
        allow_null=True,
    )
    elevation = serializers.FloatField(
        help_text=_("Elevation of the sensor, in meters."), allow_null=True
    )
    depth = serializers.FloatField(
        help_text=_("Depth of the sensor, in meters."), allow_null=True
    )
    restricted_status = serializers.ChoiceField(
        help_text=_("Restricted status of channel."),
        allow_null=True,
        choices=RestrictedStatus.choices,
    )
    description = serializers.CharField(
        help_text=_("Channel description."), allow_null=True
    )
    azimuth = serializers.FloatField(
        help_text=_(
            "Azimuth of the component in degrees clockwise from geographic (true) north."
        ),
        allow_null=True,
    )
    dip = serializers.FloatField(
        help_text=_(
            """
            Dip of the component in degrees, positive is down from horizontal.
            For horizontal dip=0, for vertical upwards dip=-90 and for vertical
            downwards dip=+90.
            """
        ),
        allow_null=True,
    )
    water_level = serializers.FloatField(
        help_text=_(
            """
            Elevation of the water surface in meters for underwater sites, where
            0 is mean sea level. If you put an OBS on a lake bottom, where the
            lake surface is at elevation=1200 meters, then you should set
            WaterLevel=1200. An OBS in the ocean would have WaterLevel=0.
            """
        ),
        allow_null=True,
    )
    sample_rate = serializers.FloatField(
        help_text=_("Sample rate in samples per second."), allow_null=True
    )
    sample_rate_ratio_number_samples = serializers.IntegerField(
        help_text=_("Integer number of samples that span a number of seconds."),
        allow_null=True,
    )
    sample_rate_ratio_number_seconds = serializers.FloatField(
        help_text=_("Integer number of seconds that span a number of samples."),
        allow_null=True,
    )
    clock_drift = serializers.FloatField(
        help_text=_(
            """
            A tolerance value, measured in seconds per sample, used as a
            threshold for time error detection in data from the channel.
            """
        ),
        allow_null=True,
    )
    calibration_units = serializers.CharField(
        help_text=_(
            """
            Symbol or name of units, e.g. "m/s", "V", "Pa", "C".
            """
        ),
        allow_null=True,
    )
    calibration_units_description = serializers.CharField(
        help_text=_(
            """
            Description of units, e.g. "Velocity in meters per second", "Volts",
            "Pascals", "Degrees Celsius".
            """
        ),
        allow_null=True,
    )
    created_at = serializers.DateTimeField(help_text=_("Channel creation date."))
    updated_at = serializers.DateTimeField(help_text=_("Channel last update date."))
    author_id = serializers.UUIDField(help_text=_("Channel author ID."))
    stream_id = serializers.CharField(help_text=_("Stream ID."))
    network_station_code = serializers.CharField(help_text=_("Network station code."))
    station_channel_code = serializers.CharField(help_text=_("Station channel code."))


class ChannelPayloadSerializer(serializers.Serializer):
    code = serializers.CharField(help_text=_("Channel code."))
    alternate_code = serializers.CharField(
        help_text=_("Alternate code used for display or association."),
        allow_null=True,
        required=False,
    )
    start_date = serializers.DateTimeField(
        help_text=_("Start date of channel."), allow_null=True, required=False
    )
    end_date = serializers.DateTimeField(
        help_text=_("End date of channel."), allow_null=True, required=False
    )
    historical_code = serializers.CharField(
        help_text=_("Historical code of channel."), allow_null=True, required=False
    )
    location_code = serializers.CharField(help_text=_("Location code of channel."))
    latitude = serializers.FloatField(
        help_text=_(
            """
            Latitude of this channel’s sensor, in degrees. Often the same as the
            station latitude, but when different the channel latitude is the true
            location of the sensor.
            """
        ),
    )
    longitude = serializers.FloatField(
        help_text=_(
            """
            Longitude of this channel’s sensor, in degrees. Often the same as the
            station longitude, but when different the channel longitude is the true
            location of the sensor.
            """
        ),
    )
    elevation = serializers.FloatField(
        help_text=_("Elevation of the sensor, in meters."),
    )
    depth = serializers.FloatField(
        help_text=_("Depth of the sensor, in meters."),
    )
    restricted_status = serializers.ChoiceField(
        help_text=_("Restricted status of channel."),
        allow_null=True,
        choices=RestrictedStatus.choices,
    )
    description = serializers.CharField(
        help_text=_("Channel description."), allow_null=True
    )
    azimuth = serializers.FloatField(
        help_text=_(
            "Azimuth of the component in degrees clockwise from geographic (true) north."
        ),
        allow_null=True,
    )
    dip = serializers.FloatField(
        help_text=_(
            """
            Dip of the component in degrees, positive is down from horizontal.
            For horizontal dip=0, for vertical upwards dip=-90 and for vertical
            downwards dip=+90.
            """
        ),
        allow_null=True,
    )
    water_level = serializers.FloatField(
        help_text=_(
            """
            Elevation of the water surface in meters for underwater sites, where
            0 is mean sea level. If you put an OBS on a lake bottom, where the
            lake surface is at elevation=1200 meters, then you should set
            WaterLevel=1200. An OBS in the ocean would have WaterLevel=0.
            """
        ),
        allow_null=True,
    )
    sample_rate = serializers.FloatField(
        help_text=_("Sample rate in samples per second."), allow_null=True
    )
    sample_rate_ratio_number_samples = serializers.IntegerField(
        help_text=_("Integer number of samples that span a number of seconds."),
        allow_null=True,
    )
    sample_rate_ratio_number_seconds = serializers.FloatField(
        help_text=_("Integer number of seconds that span a number of samples."),
        allow_null=True,
    )
    clock_drift = serializers.FloatField(
        help_text=_(
            """
            A tolerance value, measured in seconds per sample, used as a
            threshold for time error detection in data from the channel.
            """
        ),
        allow_null=True,
    )
    calibration_units = serializers.CharField(
        help_text=_(
            """
            Symbol or name of units, e.g. "m/s", "V", "Pa", "C".
            """
        ),
        allow_null=True,
    )
    calibration_units_description = serializers.CharField(
        help_text=_(
            """
            Description of units, e.g. "Velocity in meters per second", "Volts",
            "Pascals", "Degrees Celsius".
            """
        ),
        allow_null=True,
    )

    def validate_code(self, value: str) -> str:
        code = value.upper()
        if Channel.objects.filter(
            code=code, station_id=self.context["station_id"]
        ).exists():
            raise serializers.ValidationError(
                _("Channel with this code already exists")
            )
        return code

    def create(self, validated_data: dict) -> Channel:
        user = self.context["request"].user
        station_id = self.context["station_id"]
        channel = Channel.objects.create(
            author=user, station_id=station_id, **validated_data
        )
        return channel

    def update(self, instance: Channel, validated_data: dict) -> Channel:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
