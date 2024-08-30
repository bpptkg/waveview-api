from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from waveview.event.models import Attachment, Event
from waveview.event.serializers.amplitude import AmplitudeSerializer
from waveview.event.serializers.attachment import AttachmentSerializer
from waveview.event.serializers.event_type import EventTypeSerializer
from waveview.event.serializers.magnitude import MagnitudeSerializer
from waveview.event.serializers.origin import OriginSerializer
from waveview.inventory.models import Station
from waveview.users.serializers import UserSerializer


class EventSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Event ID."))
    catalog_id = serializers.UUIDField(help_text=_("Catalog ID."))
    station_of_first_arrival_id = serializers.UUIDField(
        help_text=_("Station of the first arrival ID.")
    )
    time = serializers.DateTimeField(help_text=_("Time of the event."))
    duration = serializers.FloatField(help_text=_("Duration of the event in seconds."))
    type = EventTypeSerializer()
    type_certainty = serializers.CharField(help_text=_("Event type certainty."))
    note = serializers.CharField(help_text=_("Event note."))
    method = serializers.CharField(help_text=_("Event method."))
    evaluation_mode = serializers.CharField(help_text=_("Event evaluation mode."))
    evaluation_status = serializers.CharField(help_text=_("Event evaluation status."))
    created_at = serializers.DateTimeField(help_text=_("Event creation timestamp."))
    updated_at = serializers.DateTimeField(help_text=_("Event update timestamp."))
    author = UserSerializer()
    preferred_origin = OriginSerializer(allow_null=True)
    preferred_magnitude = MagnitudeSerializer(allow_null=True)
    is_bookmarked = serializers.SerializerMethodField(
        help_text=_("True if bookmarked.")
    )

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def get_is_bookmarked(self, obj: Event) -> bool:
        user = self.context["request"].user
        return obj.bookmarked_by.filter(id=user.id).exists()


class EventDetailSerializer(EventSerializer):
    attachments = AttachmentSerializer(many=True)
    amplitudes = AmplitudeSerializer(many=True)
    magnitudes = MagnitudeSerializer(many=True)
    origins = OriginSerializer(many=True)


class EventPayloadSerializer(serializers.Serializer):
    station_of_first_arrival_id = serializers.UUIDField(
        help_text=_("Station of the first arrival ID.")
    )
    time = serializers.DateTimeField(help_text=_("Time of the event."))
    duration = serializers.FloatField(help_text=_("Duration of the event in seconds."))
    type_id = serializers.UUIDField(help_text=_("Event type ID."))
    note = serializers.CharField(
        help_text=_("Event note."), allow_blank=True, default=""
    )
    method = serializers.CharField(help_text=_("Event method."))
    evaluation_mode = serializers.CharField(help_text=_("Event evaluation mode."))
    evaluation_status = serializers.CharField(help_text=_("Event evaluation status."))
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), help_text=_("Attachment IDs.")
    )

    @transaction.atomic
    def create(self, validated_data: dict) -> Event:
        user = self.context["request"].user
        catalog_id = self.context["catalog_id"]

        station_of_first_arrival_id = validated_data["station_of_first_arrival_id"]
        time = validated_data["time"]
        duration = validated_data["duration"]
        type_id = validated_data["type_id"]
        note = validated_data["note"]
        attachment_ids = validated_data["attachment_ids"]
        method = validated_data["method"]
        evaluation_mode = validated_data["evaluation_mode"]
        evaluation_status = validated_data["evaluation_status"]

        if not Station.objects.filter(id=station_of_first_arrival_id).exists():
            raise serializers.ValidationError(
                {"station_of_first_arrival_id": _("Station does not exist.")}
            )

        event = Event.objects.create(
            catalog_id=catalog_id,
            station_of_first_arrival_id=station_of_first_arrival_id,
            time=time,
            duration=duration,
            type_id=type_id,
            note=note,
            author=user,
            method=method,
            evaluation_mode=evaluation_mode,
            evaluation_status=evaluation_status,
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
