from django.contrib import admin

from waveview.appconfig.models import (
    EventObserverConfig,
    HypocenterConfig,
    PickerConfig,
    SeismicityConfig,
)


@admin.register(PickerConfig)
class PickerConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "organization",
        "user",
        "created_at",
        "updated_at",
    )


@admin.register(HypocenterConfig)
class HypocenterConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
        "is_preferred",
        "created_at",
        "updated_at",
    )


@admin.register(SeismicityConfig)
class SeismicityConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "type",
        "order",
        "created_at",
        "updated_at",
    )
    ordering = ("order",)


@admin.register(EventObserverConfig)
class EventObserverConfigAdmin(admin.ModelAdmin):
    list_display = (
        "volcano",
        "name",
        "is_enabled",
        "created_at",
        "updated_at",
    )
