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
    is_default = serializers.BooleanField(
        help_text=_("Whether the volcano is the default one.")
    )


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


class XYZGridSerializer(serializers.Serializer):
    name = serializers.CharField(help_text=_("Grid name."))
    nx = serializers.IntegerField(help_text=_("Number of x coordinates."))
    ny = serializers.IntegerField(help_text=_("Number of y coordinates."))
    x_min = serializers.FloatField(help_text=_("Minimum x coordinate."))
    x_max = serializers.FloatField(help_text=_("Maximum x coordinate."))
    y_min = serializers.FloatField(help_text=_("Minimum y coordinate."))
    y_max = serializers.FloatField(help_text=_("Maximum y coordinate."))
    z_min = serializers.FloatField(help_text=_("Minimum z coordinate."))
    z_max = serializers.FloatField(help_text=_("Maximum z coordinate."))
    grid = serializers.JSONField(
        help_text=_(
            """
            Grid with x, y, and z coordinates. The grid is a list of tuples where
            each tuple contains the x, y, and z coordinates respectively.
            """
        )
    )


class DEMXYZSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("DEM ID."))
    volcano_id = serializers.UUIDField(help_text=_("Volcano ID."))
    name = serializers.CharField(help_text=_("DEM name."))
    utm_zone = serializers.CharField(help_text=_("UTM zone."))
    zone_number = serializers.IntegerField(help_text=_("Zone number."))
    zone_letter = serializers.CharField(help_text=_("Zone letter."))
    is_northern = serializers.BooleanField(help_text=_("Northern hemisphere."))
    x_min = serializers.FloatField(
        help_text=_(
            """
            User-defined minimum x coordinate. This is the minimum x coordinate
            that the user wants to display.
            """
        ),
        allow_null=True,
    )
    x_max = serializers.FloatField(
        help_text=_(
            """
            User-defined maximum x coordinate. This is the maximum x coordinate
            that the user wants to display.
            """
        ),
        allow_null=True,
    )
    y_min = serializers.FloatField(
        help_text=_(
            """
            User-defined minimum y coordinate. This is the minimum y coordinate
            that the user wants to display.
            """
        ),
        allow_null=True,
    )
    y_max = serializers.FloatField(
        help_text=_(
            """
            User-defined maximum y coordinate. This is the maximum y coordinate
            that the user wants to display.
            """
        ),
        allow_null=True,
    )
    z_min = serializers.FloatField(
        help_text=_(
            """
            User-defined minimum z coordinate. This is the minimum z coordinate
            that the user wants to display.
            """
        ),
        allow_null=True,
    )
    z_max = serializers.FloatField(
        help_text=_(
            """
            User-defined maximum z coordinate. This is the maximum z coordinate
            that the user wants to display.
            """
        ),
        allow_null=True,
    )
    data = XYZGridSerializer(help_text=_("DEM grid data."))
