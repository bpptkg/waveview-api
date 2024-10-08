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
from waveview.inventory.models import Network
from waveview.inventory.serializers import NetworkPayloadSerializer, NetworkSerializer
from waveview.organization.permissions import PermissionType


class NetworkDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get Network",
        operation_description=(
            """
            Get details of a seismic network within inventory. Only members of the
            organization can view the details.
            """
        ),
        tags=["Inventory"],
        responses={status.HTTP_200_OK: openapi.Response("OK", NetworkSerializer)},
    )
    def get(
        self, request: Request, organization_id: UUID, network_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        inventory = organization.inventory
        try:
            network = inventory.networks.get(id=network_id)
        except Network.DoesNotExist:
            raise NotFound(_("Network not found."))

        serializer = NetworkSerializer(network)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Network",
        operation_description=(
            """
            Update the details of an existing network. Only authorized members
            of the organization can update the network details.
            """
        ),
        tags=["Inventory"],
        request_body=NetworkPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", NetworkSerializer),
        },
    )
    def put(
        self, request: Request, organization_id: UUID, network_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to update the network.")
            )

        inventory = organization.inventory
        try:
            network = inventory.networks.get(id=network_id)
        except Network.DoesNotExist:
            raise NotFound(_("Network not found."))

        serializer = NetworkPayloadSerializer(
            network,
            data=request.data,
            partial=True,
            context={"request": request, "inventory_id": inventory.id},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Network",
        operation_description=(
            """
            Delete an existing network. Only authorized members of the
            organization can delete networks.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self, request: Request, organization_id: UUID, network_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to delete networks."))

        inventory = organization.inventory
        try:
            network = inventory.networks.get(id=network_id)
        except Network.DoesNotExist:
            raise NotFound(_("Network not found."))

        network.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
