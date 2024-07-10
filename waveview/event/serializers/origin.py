from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.models import Origin


class OriginSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Origin ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    time = serializers.DateTimeField(help_text=_("Origin time."))
    latitude = serializers.FloatField(help_text=_("Origin latitude."), allow_null=True)
    longitude = serializers.FloatField(
        help_text=_("Origin longitude."), allow_null=True
    )
    depth = serializers.FloatField(help_text=_("Origin depth."), allow_null=True)
    method = serializers.CharField(help_text=_("Origin method."), allow_null=True)
    earth_model = serializers.CharField(
        help_text=_("Origin earth model."), allow_null=True
    )
    evaluation_mode = serializers.CharField(
        help_text=_("Origin evaluation mode."), allow_null=True
    )
    evaluation_status = serializers.CharField(
        help_text=_("Origin evaluation status."), allow_null=True
    )
    created_at = serializers.DateTimeField(help_text=_("Origin created at."))
    updated_at = serializers.DateTimeField(help_text=_("Origin updated at."))
    author_id = serializers.UUIDField(help_text=_("Author ID."))


class OriginPayloadSerializer(serializers.Serializer):
    time = serializers.DateTimeField(help_text=_("Origin time."))
    latitude = serializers.FloatField(help_text=_("Origin latitude."))
    longitude = serializers.FloatField(help_text=_("Origin longitude."))
    depth = serializers.FloatField(help_text=_("Origin depth."))
    method = serializers.CharField(
        help_text=_("Origin method."), allow_null=True, allow_blank=True
    )
    earth_model = serializers.CharField(
        help_text=_("Origin earth model."), allow_null=True, allow_blank=True
    )
    evaluation_mode = serializers.CharField(
        help_text=_("Origin evaluation mode."), allow_null=True, allow_blank=True
    )
    evaluation_status = serializers.CharField(
        help_text=_("Origin evaluation status."), allow_null=True, allow_blank=True
    )

    def create(self, validated_data: dict) -> Origin:
        user = self.context["request"].user
        event_id = self.context["event_id"]
        return Origin.objects.create(event_id=event_id, author=user, **validated_data)

    def update(self, instance: Origin, validated_data: dict) -> Origin:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
