import json
import uuid

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.appconfig.models import PickerConfig, SeismicityConfig
from waveview.event.serializers.event_type import EventTypeSerializer


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


class ChannelConfigSerializer(serializers.Serializer):
    channel_id = serializers.UUIDField(help_text=_("Channel ID."))
    color = serializers.CharField(
        max_length=32, required=False, help_text=_("Default color.")
    )


class AmplitudeConfigSerializer(serializers.Serializer):
    amplitude_calculator = serializers.CharField(
        max_length=255, help_text=_("Amplitude calculator.")
    )
    channels = ChannelConfigSerializer(help_text=_("Channels."), many=True)


class PickerConfigDataSerializer(serializers.Serializer):
    helicorder_channel = ChannelConfigSerializer(help_text=_("Helicorder channel."))
    seismogram_channels = ChannelConfigSerializer(
        help_text=_("Seismogram channels."), many=True
    )
    force_center = serializers.BooleanField(help_text=_("Force center."))
    window_size = serializers.IntegerField(help_text=_("Selection window in minutes."))
    amplitude_config = AmplitudeConfigSerializer(help_text=_("Amplitude config."))


class PickerConfigSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True, help_text=_("Picker config ID."))
    user_id = serializers.UUIDField(required=False, help_text=_("Author ID."))
    name = serializers.CharField(max_length=255, help_text=_("Picker config name."))
    created_at = serializers.DateTimeField(
        read_only=True, help_text=_("Picker config creation datetime.")
    )
    updated_at = serializers.DateTimeField(
        read_only=True, help_text=_("Picker config update datetime.")
    )
    data = PickerConfigDataSerializer(help_text=_("Helicorder config."))


class PickerConfigPayloadSerializer(serializers.Serializer):
    helicorder_channel = ChannelConfigSerializer(help_text=_("Helicorder channel."))
    seismogram_channels = ChannelConfigSerializer(
        help_text=_("Seismogram channels."), many=True
    )
    force_center = serializers.BooleanField(help_text=_("Force center."))
    window_size = serializers.IntegerField(help_text=_("Selection window in minutes."))

    def create(self, validated_data: dict) -> PickerConfig:
        user = self.context["user"]
        volcano = self.context["volcano"]
        data = json.loads(json.dumps(validated_data, cls=CustomJSONEncoder))
        instance, __ = PickerConfig.objects.update_or_create(
            user=user,
            volcano=volcano,
            defaults={
                "data": data,
                "name": "Default",
            },
        )
        return instance

    def update(
        self, instance: SeismicityConfig, validated_data: dict
    ) -> SeismicityConfig:
        instance.data = validated_data
        instance.save()
        return instance


class SeismicityConfigSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(help_text=_("Seismicity ID."))
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
