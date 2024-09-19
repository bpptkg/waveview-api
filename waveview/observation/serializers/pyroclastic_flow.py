from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.observation.models import PyroclasticFlow
from waveview.observation.serializers.fall_direction import FallDirectionSerializer
from waveview.observation.models import FallDirection
from waveview.observation.choices import EventSize, ObservationForm


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
    fall_direction = FallDirectionSerializer(
        help_text=_("Pyroclastic flow fall direction.")
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
        choices=ObservationForm.choices, allow_null=True
    )
    event_size = serializers.ChoiceField(
        help_text=_("Pyroclastic flow event size."),
        choices=EventSize.choices, allow_null=True
    )
    runout_distance = serializers.FloatField(
        help_text=_("Pyroclastic flow runout distance.")
    )
    fall_direction_id = serializers.UUIDField(
        help_text=_("Pyroclastic flow fall direction ID."), allow_null=True
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

    def validate_fall_direction_id(self, value: str) -> str | None:
        if value is not None:
            try:
                FallDirection.objects.get(id=value)
            except FallDirection.DoesNotExist:
                raise serializers.ValidationError(_("Fall direction not found."))
        return value

    def create(self, validated_data: dict) -> PyroclasticFlow:
        event_id = self.context["event_id"]
        instance, __ = PyroclasticFlow.objects.update_or_create(
            event_id=event_id,
            defaults=validated_data,
        )
        return instance

    def update(
        self, instance: PyroclasticFlow, validated_data: dict
    ) -> PyroclasticFlow:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
