from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.inventory.models import Inventory
from waveview.inventory.serializers.network import NetworkWithStationsSerializer


class InventorySerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Inventory ID."))
    organization_id = serializers.UUIDField(help_text=_("Organization ID."))
    name = serializers.CharField(help_text=_("Inventory name."))
    description = serializers.CharField(help_text=_("Inventory description."))
    created_at = serializers.DateTimeField(help_text=_("Inventory creation date."))
    updated_at = serializers.DateTimeField(help_text=_("Inventory last update date."))
    author_id = serializers.UUIDField(help_text=_("Inventory author ID."))
    network_count = serializers.IntegerField(
        help_text=_("Number of networks in the inventory.")
    )
    networks = NetworkWithStationsSerializer(many=True)


class InventoryPayloadSerializer(serializers.Serializer):
    name = serializers.CharField(help_text=_("Inventory name."))
    description = serializers.CharField(help_text=_("Inventory description."))

    def create(self, validated_data: dict) -> Inventory:
        raise NotImplementedError(
            "Inventory creation is not allowed as it is automatically created "
            "when an organization is created."
        )

    def update(self, instance: Inventory, validated_data: dict) -> Inventory:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
