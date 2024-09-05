import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from waveview.observation.choices import EventSize, ObservationForm


class PyroclasticFlow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        "event.Event",
        on_delete=models.CASCADE,
        related_name="pyroclastic_flows",
        related_query_name="pyroclastic_flow",
    )
    observatory_post = models.ForeignKey(
        "ObservatoryPost", on_delete=models.SET_NULL, null=True, blank=True
    )
    occurred_at = models.DateTimeField(null=True, blank=True)
    is_lava_flow = models.BooleanField(default=False)
    observation_form = models.CharField(
        max_length=100, choices=ObservationForm.choices, null=True, blank=True
    )
    event_size = models.CharField(
        max_length=100, choices=EventSize.choices, null=True, blank=True
    )
    runout_distance = models.FloatField(null=True, blank=True)
    estimated_distance = models.FloatField(null=True, blank=True)
    fall_direction = models.ForeignKey(
        "FallDirection", on_delete=models.SET_NULL, null=True, blank=True
    )
    amplitude = models.FloatField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Pyroclastic Flow")
        verbose_name_plural = _("Pyroclastic Flows")
