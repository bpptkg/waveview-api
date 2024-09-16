from django.contrib import admin

from waveview.inventory.models import (
    Channel,
    DataSource,
    Inventory,
    InventoryFile,
    Network,
    Station,
)


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "name",
        "description",
        "created_at",
        "updated_at",
        "author",
    )


@admin.register(InventoryFile)
class InventoryFileAdmin(admin.ModelAdmin):
    list_display = (
        "inventory",
        "name",
        "file",
        "created_at",
        "updated_at",
    )


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = (
        "inventory",
        "code",
        "start_date",
        "end_date",
        "region",
        "restricted_status",
        "created_at",
        "updated_at",
        "author",
    )


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = (
        "network",
        "code",
        "start_date",
        "end_date",
        "latitude",
        "longitude",
        "elevation",
        "restricted_status",
        "created_at",
        "updated_at",
        "author",
    )


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = (
        "network",
        "station",
        "code",
        "location_code",
        "sample_rate",
        "latitude",
        "longitude",
        "elevation",
        "depth",
        "restricted_status",
        "created_at",
        "updated_at",
        "author",
    )
    ordering = ("station", "code")

    def network(self, obj: Channel) -> str:
        return obj.station.network.code


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = (
        "inventory",
        "source",
        "data",
        "created_at",
        "updated_at",
    )
