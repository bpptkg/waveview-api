from django.contrib import admin

from waveview.catalog.models import Catalog


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "is_default",
        "author",
        "created_at",
        "updated_at",
    )
