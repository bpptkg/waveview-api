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
from waveview.api.permissions import IsOrganizationMember
from waveview.organization.models import Organization, OrganizationMember, Role
from waveview.organization.permissions import PermissionType
from waveview.organization.serializers import OrganizationMemberSerializer


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
            status.HTTP_400_BAD_REQUEST: openapi.Response("Bad Request"),
            status.HTTP_403_FORBIDDEN: openapi.Response("Forbidden"),
            status.HTTP_404_NOT_FOUND: openapi.Response("Not Found"),
        },
    )
    def get(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization does not exist."))
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
            status.HTTP_200_OK: openapi.Response("OK", OrganizationMemberSerializer)
        },
    )
    def post(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization does not exist."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = request.user.has_permission(
            organization_id, PermissionType.ADD_MEMBER
        )
        if not is_author or not has_permission:
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
