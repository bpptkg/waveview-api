from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.serializers.event_type import EventTypeSerializer


class SeismicityCountByHourSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(help_text=_("Timestamp of the seismicity."))
    count = serializers.IntegerField(help_text=_("Number of events."))


class SeismicityCountByDaySerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(help_text=_("Timestamp of the seismicity."))
    count = serializers.IntegerField(help_text=_("Number of events."))


class SeismicityGroupByHourSerializer(serializers.Serializer):
    event_type = EventTypeSerializer()
    data = SeismicityCountByHourSerializer(many=True, help_text=_("Seismicity count."))


class SeismicityGroupByDaySerializer(serializers.Serializer):
    event_type = EventTypeSerializer()
    data = SeismicityCountByDaySerializer(many=True, help_text=_("Seismicity count."))
