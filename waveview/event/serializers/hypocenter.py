from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class HypocenterOriginSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Event ID."))
    event_type = serializers.CharField(help_text=_("Event type."))
    time = serializers.DateTimeField(help_text=_("Event time."))
    duration = serializers.FloatField(help_text=_("Event duration."))
    origin_id = serializers.UUIDField(help_text=_("Origin ID."))
    latitude = serializers.FloatField(help_text=_("Origin latitude in degrees."))
    latitude_uncertainty = serializers.FloatField(help_text=_("Origin latitude error."))
    longitude = serializers.FloatField(help_text=_("Hypocenter longitude in degrees."))
    longitude_uncertainty = serializers.FloatField(
        help_text=_("Origin longitude error.")
    )
    depth = serializers.FloatField(help_text=_("Origin depth in km."))
    depth_uncertainty = serializers.FloatField(help_text=_("Hypocenter depth error."))
    magnitude_value = serializers.FloatField(help_text=_("Event magnitude."))
    magnitude_type = serializers.CharField(help_text=_("Magnitude type."))


class HypocenterSerializer(serializers.Serializer):
    methods = serializers.ListField(
        child=serializers.CharField(),
        help_text=_(
            """
            List of hypocenter calculation methods. It can be used to filter
            hypocenters by method.
            """
        ),
    )
    event_types = serializers.ListField(
        child=serializers.CharField(),
        help_text=_(
            """
            List of event types. It can be used to filter hypocenters by event
            type.
            """
        ),
    )
    hypocenters = HypocenterOriginSerializer(
        many=True, help_text=_("Hypocenter origins.")
    )
