from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.event.models import Catalog
from waveview.users.serializers import UserSerializer


class CatalogSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Catalog ID."))
    volcano_id = serializers.UUIDField(help_text=_("Volcano ID."))
    name = serializers.CharField(help_text=_("Catalog name."))
    description = serializers.CharField(
        help_text=_("Catalog description."), allow_blank=True
    )
    is_default = serializers.BooleanField(
        help_text=_("Whether the catalog is the default one.")
    )
    event_count = serializers.IntegerField(
        help_text=_("Number of events in the catalog.")
    )
    created_at = serializers.DateTimeField(
        help_text=_("Date when the catalog was created.")
    )
    updated_at = serializers.DateTimeField(
        help_text=_("Date when the catalog was last updated.")
    )
    author = UserSerializer()


class CatalogPayloadSerializer(serializers.Serializer):
    name = serializers.CharField(help_text=_("Catalog name."))
    description = serializers.CharField(
        help_text=_("Catalog description."), allow_blank=True
    )

    def create(self, validated_data: dict) -> Catalog:
        user = self.context["request"].user
        volcano_id = self.context["volcano_id"]
        return Catalog.objects.create(
            author=user, volcano_id=volcano_id, **validated_data
        )

    def update(self, instance: Catalog, validated_data: dict) -> Catalog:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
