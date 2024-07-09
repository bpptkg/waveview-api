from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOwnerOrReadOnly
from waveview.organization.models import Organization
from waveview.organization.serializers import RolePayloadSerializer, RoleSerializer


class OrganizationRoleIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    @swagger_auto_schema(
        operation_id="Get Organization Roles",
        operation_description=(
            """
            Get organization roles by organization ID. Only members of the
            organization can view the roles.
            """
        ),
        tags=["Organization"],
        responses={status.HTTP_200_OK: openapi.Response("OK", RoleSerializer)},
    )
    def get(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        serializer = RoleSerializer(organization.roles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Organization Role",
        operation_description=(
            """
            Create a new role for the organization. Only organization owners can
            create roles.
            """
        ),
        tags=["Organization"],
        request_body=RolePayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", RoleSerializer)
        },
    )
    def post(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        serializer = RolePayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save(organization_id=organization_id)

        response_serializer = RoleSerializer(role)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
