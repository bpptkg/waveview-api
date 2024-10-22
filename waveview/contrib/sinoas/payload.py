from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class SinoasPayloadSerializer(serializers.Serializer):
    time = serializers.DateTimeField(help_text=_("Event time."))
    duration = serializers.FloatField(help_text=_("Event duration in seconds."))
