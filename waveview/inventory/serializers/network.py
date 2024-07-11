from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.inventory.header import RestrictedStatus
from waveview.inventory.models import Network
from waveview.inventory.serializers.station import StationWithChannelsSerializer


class NetworkSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Network ID."))
    inventory_id = serializers.UUIDField(help_text=_("Inventory ID."))
    code = serializers.CharField(help_text=_("Network code, e.g. 'VG'"))
    alternate_code = serializers.CharField(
        help_text=_("A code used for display or association."), allow_null=True
    )
    start_date = serializers.DateTimeField(
        help_text=_("Start date of network."), allow_null=True
    )
    end_date = serializers.DateTimeField(
        help_text=_("End date of network."), allow_null=True
    )
    historical_code = serializers.CharField(
        help_text=_("A previously used code if different from the current code."),
        allow_null=True,
    )
    description = serializers.CharField(
        help_text=_("Network description."), allow_null=True
    )
    region = serializers.CharField(help_text=_("Region of network."), allow_null=True)
    restricted_status = serializers.ChoiceField(
        help_text=_("Restricted status of network."),
        allow_null=True,
        choices=RestrictedStatus.choices,
    )
    created_at = serializers.DateTimeField(help_text=_("Network creation date."))
    updated_at = serializers.DateTimeField(help_text=_("Network last update date."))
    author_id = serializers.UUIDField(help_text=_("Network author ID."))
    station_count = serializers.IntegerField(
        help_text=_("Number of stations in the network.")
    )


class NetworkWithStationsSerializer(NetworkSerializer):
    stations = StationWithChannelsSerializer(many=True)


class NetworkPayloadSerializer(serializers.Serializer):
    code = serializers.CharField(help_text=_("Network code, e.g. 'VG'"))
    alternate_code = serializers.CharField(
        help_text=_("A code used for display or association."), allow_null=True
    )
    start_date = serializers.DateTimeField(
        help_text=_("Start date of network."), allow_null=True
    )
    end_date = serializers.DateTimeField(
        help_text=_("End date of network."), allow_null=True
    )
    historical_code = serializers.CharField(
        help_text=_("A previously used code if different from the current code."),
        allow_null=True,
    )
    description = serializers.CharField(
        help_text=_("Network description."), allow_null=True
    )
    region = serializers.CharField(help_text=_("Region of network."), allow_null=True)
    restricted_status = serializers.ChoiceField(
        help_text=_("Restricted status of network."),
        allow_null=True,
        choices=RestrictedStatus.choices,
    )

    def create(self, validated_data: dict) -> Network:
        user = self.context["request"].user
        inventory_id = self.context["inventory_id"]
        network = Network.objects.create(
            author=user, inventory_id=inventory_id, **validated_data
        )
        return network

    def update(self, instance: Network, validated_data: dict) -> Network:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
