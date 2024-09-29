from uuid import UUID

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.organization.models import OrganizationMember, OrganizationRole
from waveview.organization.permissions import PermissionType
from waveview.organization.serializers import OrganizationMemberSerializer


class OrganizationMemberPayloadSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(
        required=True,
        help_text=_("User ID of the member to add to the organization."),
    )
    role_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text=_("List of role IDs for the member in the organization."),
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
        if not OrganizationRole.objects.filter(id=value).exists():
            raise serializers.ValidationError(_("Role does not exist."))
        return value


class OrganizationMemberIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

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
            status.HTTP_200_OK: openapi.Response("OK", OrganizationMemberSerializer),
        },
    )
    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

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
            status.HTTP_200_OK: openapi.Response("OK", OrganizationMemberSerializer),
        },
    )
    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.ADD_MEMBER
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to add members to this organization."),
            )

        serializer = OrganizationMemberPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        organization_member, created = OrganizationMember.objects.get_or_create(
            organization_id=organization_id,
            user_id=data["user_id"],
            defaults={
                "expiration_date": data.get("expiration_date"),
                "inviter": request.user,
            },
        )
        if created:
            roles = OrganizationRole.objects.filter(id__in=data["role_ids"])
            organization_member.roles.set(roles)
        return Response(
            OrganizationMemberSerializer(organization_member).data,
            status=status.HTTP_200_OK,
        )
