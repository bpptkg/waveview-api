from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.serializers.event_type import EventTypeSerializer
from waveview.inventory.serializers import ChannelSerializer, StationSerializer
from waveview.organization_settings.models import SeismicityConfig


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
    volcano_id = serializers.UUIDField(required=False, help_text=_("Volcano ID."))
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


class SeismicityConfigSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(help_text=_("Seismicity ID."))
    organization_id = serializers.UUIDField(help_text=_("Organization ID."))
    volcano_id = serializers.UUIDField(required=False, help_text=_("Volcano ID."))
    type = EventTypeSerializer(help_text=_("Event type."))
    order = serializers.IntegerField(help_text=_("Ordering value."))
    created_at = serializers.DateTimeField(help_text=_("Seismicity creation datetime."))
    updated_at = serializers.DateTimeField(help_text=_("Seismicity update datetime."))


class SeismicityConfigPayloadSerializer(serializers.Serializer):
    type_id = serializers.UUIDField(help_text=_("Event type ID."))
    order = serializers.IntegerField(help_text=_("Ordering value."))

    def create(self, validated_data: dict) -> SeismicityConfig:
        organization_id = self.context["organization_id"]
        type_id = validated_data["type_id"]
        order = validated_data["order"]

        if SeismicityConfig.objects.filter(
            organization_id=organization_id, type_id=type_id
        ).exists():
            raise serializers.ValidationError(
                _("Seismicity configuration already exists.")
            )

        return SeismicityConfig.objects.create(
            organization_id=organization_id,
            type_id=type_id,
            order=order,
        )

    def update(
        self, instance: SeismicityConfig, validated_data: dict
    ) -> SeismicityConfig:
        instance.order = validated_data.get("order", instance.order)
        instance.save()
        return instance
