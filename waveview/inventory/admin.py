from django.contrib import admin

from waveview.inventory.models import Channel, Inventory, Network, Station


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
        "station",
        "code",
        "start_date",
        "end_date",
        "location_code",
        "latitude",
        "longitude",
        "elevation",
        "depth",
        "restricted_status",
        "created_at",
        "updated_at",
        "author",
    )
