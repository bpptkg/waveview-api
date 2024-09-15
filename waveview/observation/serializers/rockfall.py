from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.observation.models import FallDirection, Rockfall
from waveview.observation.serializers.fall_direction import FallDirectionSerializer
from waveview.observation.choices import ObservationForm, EventSize


class RockfallSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Rockfall ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    is_lava_flow = serializers.BooleanField(help_text=_("Is lava flow."))
    observation_form = serializers.ChoiceField(
        help_text=_("Rockfall observation form."), choices=ObservationForm.choices
    )
    event_size = serializers.ChoiceField(
        help_text=_("Rockfall event size."), choices=EventSize.choices
    )
    runout_distance = serializers.FloatField(help_text=_("Rockfall runout distance."))
    fall_direction = FallDirectionSerializer(help_text=_("Rockfall fall direction."))
    amplitude = serializers.FloatField(help_text=_("Rockfall amplitude."))
    duration = serializers.FloatField(help_text=_("Rockfall duration."))
    note = serializers.CharField(help_text=_("Rockfall note."), allow_null=True)
    created_at = serializers.DateTimeField(help_text=_("Rockfall creation timestamp."))
    updated_at = serializers.DateTimeField(
        help_text=_("Rockfall last update timestamp.")
    )


class RockfallPayloadSerializer(serializers.Serializer):
    is_lava_flow = serializers.BooleanField(help_text=_("Is lava flow."))
    observation_form = serializers.ChoiceField(
        help_text=_("Rockfall observation form."), choices=ObservationForm.choices
    )
    event_size = serializers.ChoiceField(
        help_text=_("Rockfall event size."), choices=EventSize.choices
    )
    runout_distance = serializers.FloatField(help_text=_("Rockfall runout distance."))
    fall_direction_id = serializers.UUIDField(
        help_text=_("Rockfall fall direction ID."), allow_null=True
    )
    amplitude = serializers.FloatField(
        help_text=_("Rockfall amplitude."), allow_null=True
    )
    duration = serializers.FloatField(
        help_text=_("Rockfall duration."), allow_null=True
    )
    note = serializers.CharField(
        help_text=_("Rockfall note."), allow_null=True, allow_blank=True
    )

    def validate_fall_direction_id(self, value: str) -> str | None:
        if value is not None:
            try:
                FallDirection.objects.get(id=value)
            except FallDirection.DoesNotExist:
                raise serializers.ValidationError(_("Fall direction not found."))
        return value

    def create(self, validated_data: dict) -> Rockfall:
        event_id = self.context["event_id"]
        instance, __ = Rockfall.objects.update_or_create(
            event_id=event_id,
            defaults=validated_data,
        )
        return instance

    def update(self, instance: Rockfall, validated_data: dict) -> Rockfall:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
