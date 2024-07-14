from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.models import EventType
from waveview.users.serializers import UserSerializer


class EventTypeSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Event type ID."))
    organization_id = serializers.UUIDField(help_text=_("Organization ID."))
    code = serializers.CharField(help_text=_("Event type code."))
    name = serializers.CharField(help_text=_("Event type name."))
    description = serializers.CharField(help_text=_("Event type description."))
    color_light = serializers.CharField(help_text=_("Event type light color."))
    color_dark = serializers.CharField(help_text=_("Event type dark color."))
    created_at = serializers.DateTimeField(
        help_text=_("Event type creation timestamp.")
    )
    updated_at = serializers.DateTimeField(help_text=_("Event type update timestamp."))
    author = UserSerializer()


class EventTypePayloadSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text=_(
            """
            Event type code, e.g., `VTA`, `VTB`, `MP`, `LF`, etc. This code
            should be unique within the organization.
            """
        )
    )
    name = serializers.CharField(
        help_text=_(
            """
            Event type name, e.g., `Volcano-Tectonic`, `Multi-Phase`,
            `Explosion`, `Eruption`, etc.
            """
        )
    )
    description = serializers.CharField(
        help_text=_(
            """
            Event type description. This can be used to provide additional
            information about the event type.
            """
        )
    )
    color_light = serializers.CharField(
        help_text=_("Event type light color for display in the UI.")
    )
    color_dark = serializers.CharField(
        help_text=_("Event type dark color for display in the UI.")
    )

    def validate_code(self, value: str) -> str:
        code = value.upper()
        if EventType.objects.filter(
            code=code, organization_id=self.context["organization_id"]
        ).exists():
            raise serializers.ValidationError(_("Event type code already exists."))
        return code

    def create(self, validated_data: dict) -> EventType:
        user = self.context["request"].user
        organization_id = self.context["organization_id"]
        return EventType.objects.create(
            organization_id=organization_id, author=user, **validated_data
        )

    def update(self, instance: EventType, validated_data: dict) -> EventType:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
