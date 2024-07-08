from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.organization.models import (
    Organization,
    OrganizationMember,
    Role,
    RoleType,
)
from waveview.organization.serializers import OrganizationMemberSerializer
from waveview.utils.uuid import is_valid_uuid


class OrganizationMemberPayloadSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(
        required=True,
        help_text=_("User ID of the member to add to the organization."),
    )
    role_id = serializers.CharField(
        required=True,
        help_text=_("Role of the member in the organization."),
    )
    expiration_date = serializers.DateTimeField(
        required=False,
        help_text=_("Expiration date of the member in the organization."),
    )

    def validate_user_id(self, value: str) -> str:
        User = get_user_model()
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError(_("User does not exist."))
        return value

    def validate_role_id(self, value: str) -> str:
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError(_("Role does not exist."))
        return value


class OrganizationMemberIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="List Organization Members",
        operation_description=(
            """
            List all members of the organization. Only organization members can
            view other members of the organization.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OrganizationMemberSerializer)
        },
    )
    def get(self, request: Request, organization_id: str) -> Response:
        if not is_valid_uuid(organization_id):
            raise serializers.ValidationError(
                {"organization_id": _("Invalid UUID format.")},
            )
        if not Organization.objects.filter(id=organization_id).exists():
            raise NotFound(_("Organization does not exist."))
        if not OrganizationMember.objects.filter(
            organization_id=organization_id, user=request.user
        ).exists():
            raise PermissionDenied(
                _("You do not have permission to view members of this organization."),
            )

        organization_members = OrganizationMember.objects.filter(
            organization_id=organization_id
        )
        return Response(
            OrganizationMemberSerializer(organization_members, many=True).data,
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_id="Add Organization Member",
        operation_description=(
            """
            Add a new member to the organization. Only organization owner can
            add new members to the organization.
            """
        ),
        tags=["Organization"],
        request_body=OrganizationMemberPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OrganizationMemberSerializer)
        },
    )
    def post(self, request: Request, organization_id: str) -> Response:
        if not is_valid_uuid(organization_id):
            raise serializers.ValidationError(
                {"organization_id": _("Invalid UUID format.")},
            )
        if not Organization.objects.filter(id=organization_id).exists():
            raise NotFound(_("Organization does not exist."))
        if not OrganizationMember.objects.filter(
            organization_id=organization_id, user=request.user, role=RoleType.OWNER
        ).exists():
            raise PermissionDenied(
                _("You do not have permission to add members to this organization."),
            )

        serializer = OrganizationMemberPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        organization_member, _ = OrganizationMember.objects.get_or_create(
            organization_id=organization_id,
            user_id=data["user_id"],
            defaults={
                "role_id": data["role_id"],
                "expiration_date": data.get("expiration_date"),
                "inviter": request.user,
            },
        )
        return Response(
            OrganizationMember(organization_member).data, status=status.HTTP_200_OK
        )
