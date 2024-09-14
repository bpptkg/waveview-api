from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.observation.models import Explosion


class ExplosionSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Explosion ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    observation_form = serializers.CharField(help_text=_("Explosion observation form."))
    column_height = serializers.FloatField(help_text=_("Explosion column height."))
    color = serializers.CharField(help_text=_("Explosion color."))
    intensity = serializers.FloatField(help_text=_("Explosion intensity."))
    vei = serializers.IntegerField(help_text=_("Explosion Volcanic Explosivity Index."))
    note = serializers.CharField(help_text=_("Explosion note."), allow_null=True)
    created_at = serializers.DateTimeField(help_text=_("Explosion creation timestamp."))
    updated_at = serializers.DateTimeField(
        help_text=_("Explosion last update timestamp.")
    )


class ExplosionPayloadSerializer(serializers.Serializer):
    observation_form = serializers.CharField(help_text=_("Explosion observation form."))
    column_height = serializers.FloatField(help_text=_("Explosion column height."))
    color = serializers.CharField(help_text=_("Explosion color."))
    intensity = serializers.FloatField(help_text=_("Explosion intensity."))
    vei = serializers.IntegerField(help_text=_("Explosion Volcanic Explosivity Index."))
    note = serializers.CharField(help_text=_("Explosion note."), allow_null=True)

    def create(self, validated_data: dict) -> Explosion:
        event_id = self.context["event_id"]
        instance, __ = Explosion.objects.update_or_create(
            event_id=event_id,
            defaults=validated_data,
        )
        return instance
