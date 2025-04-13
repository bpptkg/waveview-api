from rest_framework import serializers

from waveview.event.serializers import EventSerializer, EventTypeSerializer
from waveview.users.serializers import UserSerializer


class NewEventNotificationDataSerializer(serializers.Serializer):
    event = EventSerializer()
    actor = UserSerializer()


class EventUpdateNotificationDataSerializer(serializers.Serializer):
    event = EventSerializer()
    actor = UserSerializer()
    catalog_name = serializers.CharField()


class DeletedEvent(serializers.Serializer):
    id = serializers.UUIDField()
    type = EventTypeSerializer()
    time = serializers.DateTimeField()
    duration = serializers.FloatField()
    deleted_at = serializers.DateTimeField()


class EventDeleteNotificationDataSerializer(serializers.Serializer):
    event = DeletedEvent()
    actor = UserSerializer()
