from rest_framework import serializers

from waveview.event.serializers import EventSerializer


class NewEventNotificationDataSerializer(serializers.Serializer):
    title = serializers.CharField(default="New Event")
    event = EventSerializer()
