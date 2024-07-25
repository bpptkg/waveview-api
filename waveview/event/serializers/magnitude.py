from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.header import EvaluationStatus


class MagnitudeSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Magnitude ID."))
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    magnitude = serializers.FloatField(help_text=_("Magnitude value."))
    type = serializers.CharField(help_text=_("Magnitude type."))
    method = serializers.CharField(help_text=_("Magnitude method."))
    station_count = serializers.IntegerField(help_text=_("Number of stations."))
    azimuthal_gap = serializers.FloatField(help_text=_("Azimuthal gap."))
    evaluation_status = serializers.ChoiceField(
        help_text=_("Evaluation status."), choices=EvaluationStatus.choices
    )
    is_preferred = serializers.BooleanField(help_text=_("Is preferred magnitude."))
    created_at = serializers.DateTimeField(help_text=_("Magnitude creation timestamp."))
    updated_at = serializers.DateTimeField(help_text=_("Magnitude update timestamp."))
    author_id = serializers.UUIDField(help_text=_("Author ID."))
