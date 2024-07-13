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


class ChannelDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Channel",
        operation_description=(
            """
            Retrieve the specified channel. Only organization members can
            retrieve channels.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", ChannelSerializer),
        },
    )
    def get(
        self,
        request: Request,
        organization_id: str,
        network_id: str,
        station_id: str,
        channel_id: str,
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(network_id, "network_id")
        self.validate_uuid(station_id, "station_id")
        self.validate_uuid(channel_id, "channel_id")

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

        try:
            channel = Channel.objects.get(station=station, id=channel_id)
        except Channel.DoesNotExist:
            raise NotFound(_("Channel not found"))
        serializer = ChannelSerializer(channel)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Channel",
        operation_description=(
            """
            Update the specified channel. Only authorized organization members
            can update channels.
            """
        ),
        tags=["Inventory"],
        request_body=ChannelPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", ChannelSerializer),
        },
    )
    def put(
        self,
        request: Request,
        organization_id: str,
        network_id: str,
        station_id: str,
        channel_id: str,
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(network_id, "network_id")
        self.validate_uuid(station_id, "station_id")
        self.validate_uuid(channel_id, "channel_id")

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

        try:
            channel = Channel.objects.get(station=station, id=channel_id)
        except Channel.DoesNotExist:
            raise NotFound(_("Channel not found"))

        is_author = organization.author == request.user
        has_permission = request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not is_author and not has_permission:
            raise PermissionDenied(_("You do not have permission to update channels"))

        serializer = ChannelPayloadSerializer(channel, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Channel",
        operation_description=(
            """
            Delete the specified channel. Only authorized organization members
            can delete channels.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self,
        request: Request,
        organization_id: str,
        network_id: str,
        station_id: str,
        channel_id: str,
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(network_id, "network_id")
        self.validate_uuid(station_id, "station_id")
        self.validate_uuid(channel_id, "channel_id")

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

        try:
            channel = Channel.objects.get(station=station, id=channel_id)
        except Channel.DoesNotExist:
            raise NotFound(_("Channel not found"))

        is_author = organization.author == request.user
        has_permission = request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not is_author and not has_permission:
            raise PermissionDenied(_("You do not have permission to delete channels"))

        channel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
