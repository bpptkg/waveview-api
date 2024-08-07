from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.users.serializers import UserSerializer
from waveview.volcano.models import Volcano


class VolcanoSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Volcano ID."))
    organization_id = serializers.UUIDField(help_text=_("Organization ID."))
    name = serializers.CharField(help_text=_("Volcano name."))
    description = serializers.CharField(
        help_text=_("Volcano description."), allow_blank=True
    )
    elevation = serializers.IntegerField(
        help_text=_("Volcano elevation."), allow_null=True
    )
    location = serializers.CharField(help_text=_("Volcano location."), allow_blank=True)
    country = serializers.CharField(help_text=_("Volcano country."), allow_blank=True)
    latitude = serializers.FloatField(help_text=_("Volcano latitude."), allow_null=True)
    longitude = serializers.FloatField(
        help_text=_("Volcano longitude."), allow_null=True
    )
    created_at = serializers.DateTimeField(
        help_text=_("Date when volcano was created.")
    )
    updated_at = serializers.DateTimeField(
        help_text=_("Date when volcano was last updated.")
    )
    author = UserSerializer(help_text=_("Author of the volcano."))


class VolcanoPayloadSerializer(serializers.Serializer):
    name = serializers.CharField(help_text=_("Volcano name."))
    description = serializers.CharField(
        help_text=_("Volcano description."), allow_blank=True, required=False
    )
    elevation = serializers.IntegerField(
        help_text=_("Volcano elevation."), allow_null=True, required=False
    )
    location = serializers.CharField(
        help_text=_("Volcano location."), allow_blank=True, required=False
    )
    country = serializers.CharField(
        help_text=_("Volcano country."), allow_blank=True, required=False
    )
    latitude = serializers.FloatField(
        help_text=_("Volcano latitude."), allow_null=True, required=False
    )
    longitude = serializers.FloatField(
        help_text=_("Volcano longitude."), allow_null=True, required=False
    )

    @transaction.atomic
    def create(self, validated_data: dict) -> Volcano:
        user = self.context["request"].user
        organization_id = self.context["organization_id"]
        volcano = Volcano.objects.create(
            organization_id=organization_id, author=user, **validated_data
        )
        return volcano

    def update(self, instance: Volcano, validated_data: dict) -> Volcano:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
