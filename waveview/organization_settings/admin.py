from django.contrib import admin

from waveview.organization_settings.models import (
    HelicorderConfig,
    HypocenterConfig,
    PickerConfig,
    SeismicityConfig,
    SeismogramConfig,
    SeismogramStationConfig,
)


@admin.register(PickerConfig)
class PickerConfigAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "volcano",
        "name",
        "is_preferred",
        "created_at",
        "updated_at",
    )


@admin.register(HelicorderConfig)
class HelicorderConfigAdmin(admin.ModelAdmin):
    list_display = (
        "picker_config",
        "channel",
        "color",
        "color_light",
        "color_dark",
    )


@admin.register(SeismogramConfig)
class SeismogramConfigAdmin(admin.ModelAdmin):
    list_display = (
        "picker_config",
        "component",
    )


@admin.register(SeismogramStationConfig)
class SeismogramStationConfigAdmin(admin.ModelAdmin):
    list_display = (
        "picker_config",
        "station",
        "color",
        "color_light",
        "color_dark",
        "order",
    )

    def picker_config(self, obj: SeismogramStationConfig) -> PickerConfig:
        return obj.seismogram_config.picker_config


@admin.register(HypocenterConfig)
class HypocenterConfigAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "volcano",
        "name",
        "is_preferred",
        "created_at",
        "updated_at",
    )


@admin.register(SeismicityConfig)
class SeismicityConfigAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "type",
        "order",
        "created_at",
        "updated_at",
    )
    ordering = ("order",)
