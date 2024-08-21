from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class HypocenterOriginSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Event ID."))
    event_type = serializers.CharField(help_text=_("Event type."))
    origin_id = serializers.UUIDField(help_text=_("Origin ID."))
    latitude = serializers.FloatField(help_text=_("Hypocenter latitude."))
    latitude_uncertainty = serializers.FloatField(
        help_text=_("Hypocenter latitude error.")
    )
    longitude = serializers.FloatField(help_text=_("Hypocenter longitude."))
    longitude_uncertainty = serializers.FloatField(
        help_text=_("Hypocenter longitude error.")
    )
    depth = serializers.FloatField(help_text=_("Hypocenter depth."))
    depth_uncertainty = serializers.FloatField(help_text=_("Hypocenter depth error."))
    magnitude_value = serializers.FloatField(help_text=_("Hypocenter magnitude."))
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
    hypocenters = HypocenterOriginSerializer(
        many=True, help_text=_("Hypocenter origins.")
    )
