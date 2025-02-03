from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.observation.choices import EventSize, ObservationForm
from waveview.observation.models import FallDirection, PyroclasticFlow
from waveview.observation.serializers.fall_direction import FallDirectionSerializer


class PyroclasticFlowSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Pyroclastic flow ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    is_lava_flow = serializers.BooleanField(help_text=_("Is lava flow."))
    observation_form = serializers.ChoiceField(
        help_text=_("Pyroclastic flow observation form."),
        choices=ObservationForm.choices,
    )
    event_size = serializers.ChoiceField(
        help_text=_("Pyroclastic flow event size."),
        choices=EventSize.choices,
    )
    runout_distance = serializers.FloatField(
        help_text=_("Pyroclastic flow runout distance.")
    )
    fall_directions = FallDirectionSerializer(
        many=True, help_text=_("Pyroclastic flow fall directions.")
    )
    amplitude = serializers.FloatField(help_text=_("Pyroclastic flow amplitude."))
    duration = serializers.FloatField(help_text=_("Pyroclastic flow duration."))
    note = serializers.CharField(help_text=_("Pyroclastic flow note."), allow_null=True)
    created_at = serializers.DateTimeField(
        help_text=_("Pyroclastic flow creation timestamp.")
    )
    updated_at = serializers.DateTimeField(
        help_text=_("Pyroclastic flow last update timestamp.")
    )


class PyroclasticFlowPayloadSerializer(serializers.Serializer):
    is_lava_flow = serializers.BooleanField(help_text=_("Is lava flow."))
    observation_form = serializers.ChoiceField(
        help_text=_("Pyroclastic flow observation form."),
        choices=ObservationForm.choices,
        allow_null=True,
    )
    event_size = serializers.ChoiceField(
        help_text=_("Pyroclastic flow event size."),
        choices=EventSize.choices,
        allow_null=True,
    )
    runout_distance = serializers.FloatField(
        help_text=_("Pyroclastic flow runout distance.")
    )
    fall_direction_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_("Pyroclastic flow fall direction ID."),
        allow_null=True,
    )
    amplitude = serializers.FloatField(
        help_text=_("Pyroclastic flow amplitude."), allow_null=True
    )
    duration = serializers.FloatField(
        help_text=_("Pyroclastic flow duration."), allow_null=True
    )
    note = serializers.CharField(
        help_text=_("Pyroclastic flow note."), allow_null=True, allow_blank=True
    )

    @transaction.atomic
    def create(self, validated_data: dict) -> PyroclasticFlow:
        event_id = self.context["event_id"]
        fall_direction_ids = validated_data.pop("fall_direction_ids", [])
        instance, __ = PyroclasticFlow.objects.update_or_create(
            event_id=event_id,
            defaults=validated_data,
        )
        fall_directions = FallDirection.objects.filter(id__in=fall_direction_ids)
        instance.fall_directions.set(fall_directions)
        return instance

    @transaction.atomic
    def update(
        self, instance: PyroclasticFlow, validated_data: dict
    ) -> PyroclasticFlow:
        fall_direction_ids = validated_data.pop("fall_direction_ids", [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        fall_directions = FallDirection.objects.filter(id__in=fall_direction_ids)
        instance.fall_directions.set(fall_directions)
        return instance
