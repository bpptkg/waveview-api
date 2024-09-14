from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.observation.models import Tectonic


class TectonicSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Tectonic ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    mmi_scale = serializers.CharField(help_text=_("Tectonic MMI scale."))
    magnitude = serializers.FloatField(help_text=_("Tectonic magnitude."))
    note = serializers.CharField(help_text=_("Tectonic note."), allow_null=True)
    depth = serializers.FloatField(help_text=_("Tectonic depth."), allow_null=True)
    created_at = serializers.DateTimeField(help_text=_("Tectonic creation timestamp."))
    updated_at = serializers.DateTimeField(
        help_text=_("Tectonic last update timestamp.")
    )


class TectonicPayloadSerializer(serializers.Serializer):
    mmi_scale = serializers.CharField(
        help_text=_("Tectonic MMI scale."), allow_null=True
    )
    magnitude = serializers.FloatField(
        help_text=_("Tectonic magnitude."), allow_null=True
    )
    depth = serializers.FloatField(help_text=_("Tectonic depth."), allow_null=True)
    note = serializers.CharField(help_text=_("Tectonic note."), allow_null=True)

    def create(self, validated_data: dict) -> Tectonic:
        event_id = self.context["event_id"]
        instance, __ = Tectonic.objects.update_or_create(
            event_id=event_id,
            defaults=validated_data,
        )
        return instance
