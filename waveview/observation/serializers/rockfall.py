from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.observation.choices import EventSize, ObservationForm
from waveview.observation.models import FallDirection, Rockfall
from waveview.observation.serializers.fall_direction import FallDirectionSerializer


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
    fall_directions = FallDirectionSerializer(
        many=True, help_text=_("Rockfall fall directions.")
    )
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
        help_text=_("Rockfall observation form."),
        choices=ObservationForm.choices,
        allow_null=True,
    )
    event_size = serializers.ChoiceField(
        help_text=_("Rockfall event size."), choices=EventSize.choices, allow_null=True
    )
    runout_distance = serializers.FloatField(help_text=_("Rockfall runout distance."))
    fall_direction_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text=_("Rockfall fall direction IDs."),
        allow_null=True,
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

    @transaction.atomic
    def create(self, validated_data: dict) -> Rockfall:
        event_id = self.context["event_id"]
        fall_direction_ids = validated_data.pop("fall_direction_ids", [])
        instance, __ = Rockfall.objects.update_or_create(
            event_id=event_id,
            defaults=validated_data,
        )
        fall_directions = FallDirection.objects.filter(id__in=fall_direction_ids)
        instance.fall_directions.set(fall_directions)
        return instance

    @transaction.atomic
    def update(self, instance: Rockfall, validated_data: dict) -> Rockfall:
        fall_direction_ids = validated_data.pop("fall_direction_ids", [])
        fall_directions = FallDirection.objects.filter(id__in=fall_direction_ids)
        instance.fall_directions.set(fall_directions)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
