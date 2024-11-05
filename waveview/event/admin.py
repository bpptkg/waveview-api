from django.contrib import admin
from django.http import HttpRequest

from waveview.event.models import (
    Amplitude,
    Attachment,
    Catalog,
    Event,
    EventType,
    Magnitude,
    Origin,
    StationMagnitude,
    StationMagnitudeContribution,
)


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
        "description",
        "is_default",
        "author",
        "created_at",
        "updated_at",
    )

    def has_delete_permission(self, request: HttpRequest, obj: Catalog = None) -> None:
        return False


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "code",
        "name",
        "description",
        "color_light",
        "color_dark",
        "created_at",
        "updated_at",
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "catalog",
        "time",
        "duration",
        "type",
        "author",
        "created_at",
        "updated_at",
    )
    ordering = ("-time",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "media_type",
        "name",
        "author",
        "uploaded_at",
    )


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "time",
        "latitude",
        "longitude",
        "depth",
        "method",
        "earth_model",
        "evaluation_mode",
        "evaluation_status",
        "is_preferred",
        "author",
        "created_at",
        "updated_at",
    )


@admin.register(Magnitude)
class MagnitudeAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "magnitude",
        "type",
        "method",
        "station_count",
        "azimuthal_gap",
        "evaluation_status",
        "is_preferred",
        "created_at",
        "updated_at",
        "author",
    )


@admin.register(Amplitude)
class AmplitudeAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "amplitude",
        "type",
        "category",
        "unit",
        "waveform",
        "method",
        "evaluation_mode",
        "is_preferred",
        "author",
    )


@admin.register(StationMagnitude)
class StationMagnitudeAdmin(admin.ModelAdmin):
    list_display = (
        "amplitude",
        "magnitude",
        "type",
        "method",
        "author",
    )


@admin.register(StationMagnitudeContribution)
class StationMagnitudeContributionAdmin(admin.ModelAdmin):
    list_display = (
        "magnitude",
        "station_magnitude",
        "residual",
        "weight",
    )
