from django.contrib import admin

from waveview.event.models import (
    Catalog,
    Event,
    EventType,
    Attachment,
    Origin,
    Magnitude,
    Amplitude,
    StationMagnitude,
    StationMagnitudeContribution,
)


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "volcano",
        "name",
        "description",
        "is_default",
        "author",
        "created_at",
        "updated_at",
    )


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
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
        "id",
        "catalog",
        "time",
        "duration",
        "type",
        "station_of_first_arrival",
        "author",
        "created_at",
        "updated_at",
    )


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event",
        "media_type",
        "name",
        "author",
        "uploaded_at",
    )


@admin.register(Origin)
class OriginAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event",
        "time",
        "latitude",
        "longitude",
        "depth",
        "method",
        "earth_model",
        "evaluation_mode",
        "evaluation_status",
        "author",
        "created_at",
        "updated_at",
    )


@admin.register(Magnitude)
class MagnitudeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
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
        "id",
        "event",
        "amplitude",
        "type",
        "category",
        "time",
        "begin",
        "end",
        "snr",
        "unit",
        "waveform",
        "method",
        "evaluation_mode",
        "is_preferred",
        "created_at",
        "updated_at",
        "author",
    )


@admin.register(StationMagnitude)
class StationMagnitudeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "amplitude",
        "magnitude",
        "type",
        "method",
        "created_at",
        "updated_at",
        "author",
    )


@admin.register(StationMagnitudeContribution)
class StationMagnitudeContributionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "magnitude",
        "station_magnitude",
        "residual",
        "weight",
    )
