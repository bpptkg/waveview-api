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
from waveview.inventory.models import Station
from waveview.inventory.serializers import StationPayloadSerializer, StationSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class StationDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Station",
        operation_description=(
            """
            Retrieve the specified station.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", StationSerializer),
            status.HTTP_404_NOT_FOUND: openapi.Response("Not Found"),
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
        serializer = StationSerializer(station)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Station",
        operation_description=(
            """
            Update the specified station.
            """
        ),
        tags=["Inventory"],
        request_body=StationPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", StationSerializer),
            status.HTTP_400_BAD_REQUEST: openapi.Response("Bad Request"),
            status.HTTP_403_FORBIDDEN: openapi.Response("Forbidden"),
            status.HTTP_404_NOT_FOUND: openapi.Response("Not Found"),
        },
    )
    def put(
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
            raise PermissionDenied(_("You do not have permission to update stations"))

        serializer = StationPayloadSerializer(station, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Station",
        operation_description=(
            """
            Delete the specified station.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
            status.HTTP_403_FORBIDDEN: openapi.Response("Forbidden"),
            status.HTTP_404_NOT_FOUND: openapi.Response("Not Found"),
        },
    )
    def delete(
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
            raise PermissionDenied(_("You do not have permission to delete stations"))

        station.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
