from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.models import SeismicityConfig
from waveview.event.serializers.event_type import EventTypeSerializer


class SeismicityCountByHourSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(help_text=_("Timestamp of the seismicity."))
    count = serializers.IntegerField(help_text=_("Number of events."))


class SeismicityCountByDaySerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(help_text=_("Timestamp of the seismicity."))
    count = serializers.IntegerField(help_text=_("Number of events."))


class SeismicityGroupByHourSerializer(serializers.Serializer):
    event_type = EventTypeSerializer()
    data = SeismicityCountByHourSerializer(many=True, help_text=_("Seismicity count."))


class SeismicityGroupByDaySerializer(serializers.Serializer):
    event_type = EventTypeSerializer()
    data = SeismicityCountByDaySerializer(many=True, help_text=_("Seismicity count."))


class SeismicityConfigSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(help_text=_("Seismicity ID."))
    organization_id = serializers.UUIDField(help_text=_("Organization ID."))
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
