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
from waveview.inventory.models import Network, Station
from waveview.inventory.serializers import StationPayloadSerializer, StationSerializer
from waveview.organization.permissions import PermissionType


class StationIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Stations",
        operation_description=(
            """
            List all stations in the specified network.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", StationSerializer(many=True)),
        },
    )
    def get(
        self, request: Request, organization_id: UUID, network_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        inventory = organization.inventory
        stations = Station.objects.filter(
            network__inventory=inventory, network_id=network_id
        ).all()
        serializer = StationSerializer(stations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Station",
        operation_description=(
            """
            Create a new station in the specified network. Only authorized
            organization members can create stations.
            """
        ),
        tags=["Inventory"],
        request_body=StationPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", StationSerializer),
        },
    )
    def post(
        self, request: Request, organization_id: UUID, network_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to create stations"))

        inventory = organization.inventory
        try:
            network = inventory.networks.get(id=network_id)
        except Network.DoesNotExist:
            raise NotFound(_("Network not found"))

        serializer = StationPayloadSerializer(
            data=request.data, context={"request": request, "network_id": network.id}
        )
        serializer.is_valid(raise_exception=True)
        station = serializer.save(network=network)
        return Response(StationSerializer(station).data, status=status.HTTP_201_CREATED)
