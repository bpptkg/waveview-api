from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.inventory.serializers import NetworkPayloadSerializer, NetworkSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class NetworkIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Networks",
        operation_description=(
            """
            Get list of seismic networks within inventory. Only members of the
            organization can view the details.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", NetworkSerializer),
        },
    )
    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        inventory = organization.inventory
        networks = inventory.networks.all()
        serializer = NetworkSerializer(networks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Network",
        operation_description=(
            """
            Create a new network. Only authorized members of the organization
            can create new networks.
            """
        ),
        tags=["Inventory"],
        request_body=NetworkPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", NetworkSerializer),
        },
    )
    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to create networks."))

        inventory = organization.inventory
        serializer = NetworkPayloadSerializer(
            data=request.data,
            context={"request": request, "inventory_id": inventory.id},
        )
        serializer.is_valid(raise_exception=True)
        network = serializer.save()
        return Response(NetworkSerializer(network).data, status=status.HTTP_201_CREATED)
