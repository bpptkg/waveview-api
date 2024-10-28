from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.header import AmplitudeCategory, EvaluationMode


class AmplitudeSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Amplitude ID."))
    amplitude = serializers.FloatField(help_text=_("Amplitude value."))
    type = serializers.CharField(help_text=_("Amplitude type."))
    category = serializers.ChoiceField(
        help_text=_("Amplitude category."), choices=AmplitudeCategory.choices
    )
    time = serializers.DateTimeField(
        help_text=_("Reference point in time or central point.")
    )
    begin = serializers.FloatField(
        help_text=_("Duration of time interval before reference point in time window.")
    )
    end = serializers.FloatField(
        help_text=_("Duration of time interval after reference point in time window.")
    )
    duration = serializers.FloatField(help_text=_("Amplitude period."))
    snr = serializers.FloatField(help_text=_("Signal-to-noise ratio."))
    unit = serializers.CharField(help_text=_("Amplitude unit."))
    waveform_id = serializers.UUIDField(help_text=_("Waveform ID."))
    label = serializers.CharField(help_text=_("Amplitude label."))
    method = serializers.CharField(help_text=_("Amplitude method."))
    evaluation_mode = serializers.ChoiceField(
        help_text=_("Evaluation mode."), choices=EvaluationMode.choices
    )
    is_preferred = serializers.BooleanField(help_text=_("Is preferred amplitude."))
    created_at = serializers.DateTimeField(help_text=_("Amplitude creation timestamp."))
    updated_at = serializers.DateTimeField(help_text=_("Amplitude update timestamp."))
    author_id = serializers.UUIDField(help_text=_("Author ID."))
