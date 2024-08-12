from django.contrib import admin

from waveview.picker.models import (
    HelicorderConfig,
    PickerConfig,
    SeismogramConfig,
    SeismogramStationConfig,
)


@admin.register(PickerConfig)
class PickerConfigAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "name",
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
