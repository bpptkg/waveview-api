from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.organization.models import Organization, OrganizationMember, Role
from waveview.organization.permissions import PermissionType
from waveview.organization.serializers import OrganizationMemberSerializer


class OrganizationMemberUpdatePayloadSerializer(serializers.Serializer):
    role_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_("List of role IDs the member can have in the organization."),
    )
    expiration_date = serializers.DateTimeField(
        required=False,
        help_text=_("Expiration date of the member in the organization."),
    )

    def validate_role_id(self, value: str) -> str:
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError(_("Role does not exist."))
        return value

    def update(
        self, instance: OrganizationMember, validated_data: dict
    ) -> OrganizationMember:
        role_ids = validated_data.get("role_ids")
        if role_ids:
            roles = Role.objects.filter(id__in=role_ids)
            instance.roles.set(roles)
        instance.expiration_date = validated_data.get(
            "expiration_date", instance.expiration_date
        )
        instance.save()
        return instance


class OrganizationMemberDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Organization Member",
        operation_description=(
            """
            Retrieve a member in the organization. Only organization members can
            retrieve other members in the organization.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OrganizationMemberSerializer),
        },
    )
    def get(self, request: Request, organization_id: UUID, user_id: UUID) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization does not exist."))
        self.check_object_permissions(request, organization)

        organization_member = OrganizationMember.objects.get(
            organization_id=organization_id, user_id=user_id
        )
        return Response(
            OrganizationMemberSerializer(organization_member).data,
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_id="Update Organization Member",
        operation_description=(
            """
            Update the role and expiration date of a member in the organization.
            Only organization owner or admin can update the role and expiration
            date of members in the organization.
            """
        ),
        tags=["Organization"],
        request_body=OrganizationMemberUpdatePayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OrganizationMemberSerializer),
        },
    )
    def put(self, request: Request, organization_id: UUID, user_id: UUID) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization does not exist."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.UPDATE_MEMBER
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to update members in this organization."),
            )

        organization_member = OrganizationMember.objects.get(
            organization_id=organization_id, user_id=user_id
        )
        serializer = OrganizationMemberUpdatePayloadSerializer(
            organization_member, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        organization_member = serializer.save()
        return Response(
            OrganizationMemberSerializer(organization_member).data,
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_id="Remove Organization Member",
        operation_description=(
            """
            Remove a member from the organization. Only organization owner or
            admin can remove members from the organization.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self, request: Request, organization_id: UUID, user_id: UUID
    ) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization does not exist."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.REMOVE_MEMBER
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to remove members in this organization."),
            )

        OrganizationMember.objects.filter(
            organization_id=organization_id, user_id=user_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
