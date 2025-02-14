from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.header import EvaluationMode, EvaluationStatus
from waveview.event.models import Origin


class OriginSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Origin ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    time = serializers.DateTimeField(help_text=_("Origin time."))
    latitude = serializers.FloatField(
        help_text=_("Origin latitude in degree."), allow_null=True
    )
    longitude = serializers.FloatField(
        help_text=_("Origin longitude in degree."), allow_null=True
    )
    depth = serializers.FloatField(help_text=_("Origin depth in km."), allow_null=True)
    method = serializers.CharField(help_text=_("Origin method name."), allow_null=True)
    earth_model = serializers.CharField(
        help_text=_("Origin earth model name."), allow_null=True
    )
    evaluation_mode = serializers.ChoiceField(
        help_text=_("Origin evaluation mode."),
        allow_null=True,
        choices=EvaluationMode.choices,
    )
    evaluation_status = serializers.ChoiceField(
        help_text=_("Origin evaluation status."),
        allow_null=True,
        choices=EvaluationStatus.choices,
    )
    created_at = serializers.DateTimeField(help_text=_("Origin created at."))
    updated_at = serializers.DateTimeField(help_text=_("Origin updated at."))
    author_id = serializers.UUIDField(help_text=_("Author ID."))
    is_preferred = serializers.BooleanField(
        help_text=_("True if this origin is preferred.")
    )


class OriginPayloadSerializer(serializers.Serializer):
    time = serializers.DateTimeField(help_text=_("Origin time in ISO 8601 format."))
    latitude = serializers.FloatField(help_text=_("Origin latitude in degree."))
    longitude = serializers.FloatField(help_text=_("Origin longitude in degree."))
    depth = serializers.FloatField(help_text=_("Origin depth in km."))
    method = serializers.CharField(
        help_text=_(
            "Method name used to calculate the origin, e.g. btbb, hypo71, etc."
        ),
        allow_null=True,
        allow_blank=True,
    )
    earth_model = serializers.CharField(
        help_text=_("Origin earth model name."), allow_null=True, allow_blank=True
    )
    evaluation_mode = serializers.ChoiceField(
        choices=EvaluationMode.choices,
        help_text=_("Origin evaluation mode."),
        allow_null=True,
        allow_blank=True,
    )
    evaluation_status = serializers.ChoiceField(
        choices=EvaluationStatus.choices,
        help_text=_("Origin evaluation status."),
        allow_null=True,
        allow_blank=True,
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
