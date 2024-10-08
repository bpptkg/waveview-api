from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.observation.models import VolcanicEmission
from waveview.observation.choices import ObservationForm


class VolcanicEmissionSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Volcanic emission ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    observation_form = serializers.CharField(
        help_text=_("Volcanic emission observation form.")
    )
    height = serializers.FloatField(help_text=_("Volcanic emission height."))
    color = serializers.CharField(help_text=_("Volcanic emission color."))
    intensity = serializers.FloatField(help_text=_("Volcanic emission intensity."))
    note = serializers.CharField(
        help_text=_("Volcanic emission note."), allow_null=True
    )
    created_at = serializers.DateTimeField(
        help_text=_("Volcanic emission creation timestamp.")
    )
    updated_at = serializers.DateTimeField(
        help_text=_("Volcanic emission last update timestamp.")
    )


class VolcanicEmissionPayloadSerializer(serializers.Serializer):
    observation_form = serializers.ChoiceField(
        help_text=_("Volcanic emission observation form."),
        choices=ObservationForm.choices,
        allow_null=True,
    )
    height = serializers.FloatField(help_text=_("Volcanic emission height."))
    color = serializers.CharField(
        help_text=_("Volcanic emission color."), allow_null=True, allow_blank=True
    )
    intensity = serializers.FloatField(help_text=_("Volcanic emission intensity."))
    note = serializers.CharField(
        help_text=_("Volcanic emission note."), allow_null=True, allow_blank=True
    )

    def validate_color(self, value: str) -> str | None:
        if not value:
            return None
        return value

    def create(self, validated_data: dict) -> VolcanicEmission:
        event_id = self.context["event_id"]
        instance, __ = VolcanicEmission.objects.update_or_create(
            event_id=event_id,
            defaults=validated_data,
        )
        return instance

    def update(
        self, instance: VolcanicEmission, validated_data: dict
    ) -> VolcanicEmission:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
