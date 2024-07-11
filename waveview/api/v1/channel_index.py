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
from waveview.inventory.models import Channel, Station
from waveview.inventory.serializers import ChannelPayloadSerializer, ChannelSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class ChannelIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Channels",
        operation_description=(
            """
            List all channels in the specified station.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", ChannelSerializer(many=True)),
        },
    )
    def get(
        self, request: Request, organization_id: str, network_id: str, station_id: str
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(network_id, "network_id")
        self.validate_uuid(station_id, "station_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found"))
        self.check_object_permissions(request, organization)

        inventory = organization.inventory
        try:
            station = Station.objects.get(
                network__inventory=inventory, network_id=network_id, id=station_id
            )
        except Station.DoesNotExist:
            raise NotFound(_("Station not found"))

        channels = Channel.objects.filter(station=station).all()
        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Channel",
        operation_description=(
            """
            Create a new channel in the specified station. Only authorized
            organization members can create channels.
            """
        ),
        tags=["Inventory"],
        request_body=ChannelPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", ChannelSerializer),
            status.HTTP_400_BAD_REQUEST: openapi.Response("Bad Request"),
        },
    )
    def post(
        self, request: Request, organization_id: str, network_id: str, station_id: str
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(network_id, "network_id")
        self.validate_uuid(station_id, "station_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found"))
        self.check_object_permissions(request, organization)

        inventory = organization.inventory
        try:
            station = Station.objects.get(
                network__inventory=inventory, network_id=network_id, id=station_id
            )
        except Station.DoesNotExist:
            raise NotFound(_("Station not found"))

        is_author = organization.author == request.user
        has_permission = request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not is_author and not has_permission:
            raise PermissionDenied(_("You do not have permission to create channels"))

        serializer = ChannelPayloadSerializer(
            data=request.data, context={"request": request, "station_id": station.id}
        )
        serializer.is_valid(raise_exception=True)
        channel = serializer.save(station=station)
        return Response(ChannelSerializer(channel).data, status=status.HTTP_201_CREATED)
