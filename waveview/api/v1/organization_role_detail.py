from uuid import UUID

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
from waveview.organization.models import Organization, OrganizationRole
from waveview.organization.serializers import OrganizationRolePayloadSerializer, OrganizationRoleSerializer


class OrganizationRoleDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    @swagger_auto_schema(
        operation_id="Retrieve Organization Role",
        operation_description=(
            """
            Get organization role detail by organization ID and role ID. Only
            members of the organization can view the role details.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OrganizationRoleSerializer),
        },
    )
    def get(self, request: Request, organization_id: UUID, role_id: UUID) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            role = organization.organization_roles.get(id=role_id)
        except OrganizationRole.DoesNotExist:
            raise NotFound(_("Role not found."))

        serializer = OrganizationRoleSerializer(role)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Organization Role",
        operation_description=(
            """
            Update the details of an existing organization role. Only organization
            owners can update roles.
            """
        ),
        tags=["Organization"],
        request_body=OrganizationRolePayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OrganizationRoleSerializer),
        },
    )
    def put(self, request: Request, organization_id: UUID, role_id: UUID) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            role = organization.organization_roles.get(id=role_id)
        except OrganizationRole.DoesNotExist:
            raise NotFound(_("Role not found."))

        serializer = OrganizationRolePayloadSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        role = serializer.update(role, serializer.validated_data)
        return Response(OrganizationRoleSerializer(role).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Organization Role",
        operation_description=(
            """
            Delete an existing organization role. Only organization owners can delete
            roles.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self, request: Request, organization_id: UUID, role_id: UUID
    ) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            role = organization.organization_roles.get(id=role_id)
        except OrganizationRole.DoesNotExist:
            raise NotFound(_("Role not found."))

        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
