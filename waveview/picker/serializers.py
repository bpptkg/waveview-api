from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.inventory.serializers import ChannelSerializer, StationSerializer


class SeismogramStationConfigSerializer(serializers.Serializer):
    station = StationSerializer()
    color = serializers.CharField(
        max_length=32, required=False, help_text=_("Default color.")
    )
    color_light = serializers.CharField(
        max_length=32, required=False, help_text=_("Light color.")
    )
    color_dark = serializers.CharField(
        max_length=32, required=False, help_text=_("Dark color.")
    )
    order = serializers.IntegerField(required=False, help_text=_("Ordering value."))


class SeismogramConfigSerializer(serializers.Serializer):
    component = serializers.CharField(
        max_length=32, required=False, help_text=_("Component.")
    )
    station_configs = SeismogramStationConfigSerializer(
        many=True, required=False, help_text=_("Station configs.")
    )


class HelicorderConfigSerializer(serializers.Serializer):
    channel = ChannelSerializer()
    color = serializers.CharField(
        max_length=32, required=False, help_text=_("Default color.")
    )
    color_light = serializers.CharField(
        max_length=32, required=False, help_text=_("Light color.")
    )
    color_dark = serializers.CharField(
        max_length=32, required=False, help_text=_("Dark color.")
    )


class PickerConfigSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, help_text=_("Picker config ID."))
    organization_id = serializers.UUIDField(help_text=_("Organization ID."))
    name = serializers.CharField(max_length=255, help_text=_("Picker config name."))
    created_at = serializers.DateTimeField(
        read_only=True, help_text=_("Picker config creation datetime.")
    )
    updated_at = serializers.DateTimeField(
        read_only=True, help_text=_("Picker config update datetime.")
    )
    author_id = serializers.UUIDField(required=False, help_text=_("Author ID."))
    helicorder_config = HelicorderConfigSerializer(help_text=_("Helicorder config."))
    seismogram_config = SeismogramConfigSerializer(help_text=_("Seismogram config."))
