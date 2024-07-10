from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.models import Attachment, Event
from waveview.event.serializers.attachment import AttachmentSerializer
from waveview.event.serializers.event_type import EventTypeSerializer
from waveview.event.serializers.origin import OriginSerializer
from waveview.users.serializers import UserSerializer


class EventSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Event ID."))
    catalog_id = serializers.UUIDField(help_text=_("Catalog ID."))
    type = EventTypeSerializer()
    note = serializers.CharField(help_text=_("Event note."))
    attachments = AttachmentSerializer(many=True)
    created_at = serializers.DateTimeField(help_text=_("Event creation timestamp."))
    updated_at = serializers.DateTimeField(help_text=_("Event update timestamp."))
    author = UserSerializer()
    preferred_origin = OriginSerializer(allow_null=True)


class EventPayloadSerializer(serializers.Serializer):
    type_id = serializers.UUIDField(help_text=_("Event type ID."))
    note = serializers.CharField(help_text=_("Event note."))
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), help_text=_("Attachment IDs.")
    )

    @transaction.atomic
    def create(self, validated_data: dict) -> Event:
        user = self.context["request"].user
        catalog_id = self.context["catalog_id"]

        type_id = validated_data["type_id"]
        note = validated_data["note"]
        attachment_ids = validated_data["attachment_ids"]

        event = Event.objects.create(
            catalog_id=catalog_id,
            type_id=type_id,
            note=note,
            author=user,
        )
        Attachment.objects.filter(id__in=attachment_ids).update(event=event)
        return event

    @transaction.atomic
    def update(self, instance: Event, validated_data: dict) -> Event:
        attachment_ids = validated_data.pop("attachment_ids", [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        Attachment.objects.filter(id__in=attachment_ids).update(event=instance)
        return instance
