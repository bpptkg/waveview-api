from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from waveview.inventory.models import Inventory
from waveview.organization.models import (
    Organization,
    OrganizationRole,
)
from waveview.organization.permissions import PermissionType
from waveview.users.serializers import UserSerializer


class OrganizationRoleSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Organization role ID."))
    slug = serializers.SlugField(help_text=_("Organization role slug."))
    name = serializers.CharField(help_text=_("Organization role name."))
    description = serializers.CharField(help_text=_("Organization role description."))
    permissions = serializers.ListField(
        help_text=_("List of permissions for the organization role.")
    )
    order = serializers.IntegerField(help_text=_("Order of the organization role."))


class OrganizationMemberSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Organization member ID."))
    user = UserSerializer()
    roles = OrganizationRoleSerializer(many=True)
    date_added = serializers.DateTimeField(
        help_text=_("Date when the user was added to the organization.")
    )
    expiration_date = serializers.DateTimeField(
        help_text=_("Date when the user's membership expires."), allow_null=True
    )
    inviter = UserSerializer()


class OrganizationSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("Organization ID."))
    slug = serializers.SlugField(help_text=_("Organization slug."))
    name = serializers.CharField(help_text=_("Organization name."))
    email = serializers.EmailField(help_text=_("Organization email."))
    description = serializers.CharField(
        help_text=_("Organization description."), allow_blank=True
    )
    url = serializers.URLField(help_text=_("Organization URL."), allow_blank=True)
    address = serializers.CharField(
        help_text=_("Organization address."), allow_blank=True
    )
    avatar = serializers.ImageField(
        help_text=_("Organization avatar."), allow_null=True
    )
    author = UserSerializer(required=False)
    created_at = serializers.DateTimeField(
        help_text=_("Date when the organization was created.")
    )
    updated_at = serializers.DateTimeField(
        help_text=_("Date when the organization was last updated.")
    )
    member_count = serializers.IntegerField(
        help_text=_("Number of organization members.")
    )


class OrganizationPayloadSerializer(serializers.Serializer):
    slug = serializers.SlugField(help_text=_("Organization slug."))
    name = serializers.CharField(help_text=_("Organization name."))
    email = serializers.EmailField(help_text=_("Organization email."))
    description = serializers.CharField(
        help_text=_("Organization description."), allow_blank=True, required=False
    )
    url = serializers.URLField(
        help_text=_("Organization URL."), allow_blank=True, required=False
    )
    address = serializers.CharField(
        help_text=_("Organization address."), allow_blank=True, required=False
    )
    avatar = serializers.ImageField(
        help_text=_("Organization avatar."),
        required=False,
        allow_null=True,
        allow_empty_file=True,
    )

    def validate_slug(self, value: str) -> str:
        if Organization.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                _("Organization with this slug already exists.")
            )
        return value

    @transaction.atomic
    def create(self, validated_data: dict) -> Organization:
        user = self.context["request"].user
        organization = Organization.objects.create(author=user, **validated_data)
        Inventory.objects.create(
            organization=organization, name="Inventory", author=user
        )
        return organization

    def update(self, instance: Organization, validated_data: dict) -> Organization:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class OrganizationRolePayloadSerializer(serializers.Serializer):
    slug = serializers.SlugField(help_text=_("Organization role slug."))
    name = serializers.CharField(help_text=_("Organization role name."))
    description = serializers.CharField(help_text=_("Organization role description."))
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=PermissionType.values),
        help_text=_("List of permissions for the organization role."),
    )
    order = serializers.IntegerField(help_text=_("Order of the organization role."))

    def validate_slug(self, value: str) -> str:
        if OrganizationRole.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                _("OrganizationRole with this slug already exists.")
            )
        return value

    def create(self, validated_data: dict) -> OrganizationRole:
        organization_id = self.context["organization_id"]
        role = OrganizationRole.objects.create(
            organization_id=organization_id, **validated_data
        )
        return role

    def update(
        self, instance: OrganizationRole, validated_data: dict
    ) -> OrganizationRole:
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance


class OrganizationSettingsSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text=_("ID."))
    organization_id = serializers.UUIDField(help_text=_("Organization ID."))
    data = serializers.JSONField(help_text=_("Data."))
