from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.inventory.header import RestrictedStatus
from waveview.inventory.models import Station
from waveview.inventory.serializers.channel import ChannelSerializer


class StationSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Station ID."))
    network_id = serializers.UUIDField(help_text=_("Network ID."))
    code = serializers.CharField(help_text=_("Station code."))
    alternate_code = serializers.CharField(
        help_text=_("Alternate code used for display or association."), allow_null=True
    )
    start_date = serializers.DateTimeField(
        help_text=_("Start date of station."), allow_null=True
    )
    end_date = serializers.DateTimeField(
        help_text=_("End date of station."), allow_null=True
    )
    historical_code = serializers.CharField(
        help_text=_("Historical code of station."), allow_null=True
    )
    latitude = serializers.FloatField(
        help_text=_("Station latitude, in degrees."), allow_null=True
    )
    longitude = serializers.FloatField(
        help_text=_("Station longitude, in degrees."), allow_null=True
    )
    elevation = serializers.FloatField(
        help_text=_("Station elevation, in meters."), allow_null=True
    )
    restricted_status = serializers.ChoiceField(
        help_text=_("Restricted status of station."),
        allow_null=True,
        choices=RestrictedStatus.choices,
    )
    description = serializers.CharField(
        help_text=_("Station description."), allow_null=True
    )
    place = serializers.CharField(
        help_text=_("Place where the station is located."), allow_null=True
    )
    country = serializers.CharField(
        help_text=_("Country where the station is located."), allow_null=True
    )
    created_at = serializers.DateTimeField(help_text=_("Station creation date."))
    updated_at = serializers.DateTimeField(help_text=_("Station last update date."))
    author_id = serializers.UUIDField(help_text=_("Station author ID."))
    channel_count = serializers.IntegerField(
        help_text=_("Number of channels in the station.")
    )


class StationWithChannelsSerializer(StationSerializer):
    channels = ChannelSerializer(many=True)


class StationPayloadSerializer(serializers.Serializer):
    code = serializers.CharField(help_text=_("Station code."))
    alternate_code = serializers.CharField(
        help_text=_("Alternate code used for display or association."),
        allow_null=True,
        required=False,
    )
    start_date = serializers.DateTimeField(
        help_text=_("Start date of station."), allow_null=True, required=False
    )
    end_date = serializers.DateTimeField(
        help_text=_("End date of station."), allow_null=True, required=False
    )
    historical_code = serializers.CharField(
        help_text=_("Historical code of station."), allow_null=True, required=False
    )
    latitude = serializers.FloatField(
        help_text=_("Station latitude, in degrees."), allow_null=True, required=False
    )
    longitude = serializers.FloatField(
        help_text=_("Station longitude, in degrees."), allow_null=True, required=False
    )
    elevation = serializers.FloatField(
        help_text=_("Station elevation, in meters."), allow_null=True, required=False
    )
    restricted_status = serializers.ChoiceField(
        help_text=_("Restricted status of station."),
        allow_null=True,
        choices=RestrictedStatus.choices,
        required=False,
    )
    description = serializers.CharField(
        help_text=_("Station description."), allow_null=True, required=False
    )
    place = serializers.CharField(
        help_text=_("Place where the station is located."),
        allow_null=True,
        required=False,
    )
    country = serializers.CharField(
        help_text=_("Country where the station is located."),
        allow_null=True,
        required=False,
    )

    def validate_code(self, value: str) -> str:
        code = value.upper()
        if Station.objects.filter(
            code=code, network_id=self.context["network_id"]
        ).exists():
            raise serializers.ValidationError(
                _("Station with this code already exists")
            )
        return code

    def create(self, validated_data: dict) -> Station:
        user = self.context["request"].user
        network_id = self.context["network_id"]
        station = Station.objects.create(
            author=user, network_id=network_id, **validated_data
        )
        return station

    def update(self, instance: Station, validated_data: dict) -> Station:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
