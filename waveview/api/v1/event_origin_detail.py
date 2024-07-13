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
from waveview.event.models import Event, Origin
from waveview.event.serializers import OriginPayloadSerializer, OriginSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class EventOriginDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Origin",
        operation_description=(
            """
            Retrieve an origin of an event in the catalog.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OriginSerializer),
        },
    )
    def get(
        self,
        request: Request,
        organization_id: str,
        catalog_id: str,
        event_id: str,
        origin_id: str,
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(catalog_id, "catalog_id")
        self.validate_uuid(event_id, "event_id")
        self.validate_uuid(origin_id, "origin_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            event = Event.objects.get(catalog_id=catalog_id, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        try:
            origin = event.origins.get(id=origin_id)
        except Origin.DoesNotExist:
            raise NotFound(_("Origin not found."))

        serializer = OriginSerializer(origin)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Origin",
        operation_description=(
            """
            Update an origin of an event in the catalog.
            """
        ),
        tags=["Event"],
        request_body=OriginPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OriginSerializer),
        },
    )
    def put(
        self,
        request: Request,
        organization_id: str,
        catalog_id: str,
        event_id: str,
        origin_id: str,
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(catalog_id, "catalog_id")
        self.validate_uuid(event_id, "event_id")
        self.validate_uuid(origin_id, "origin_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.UPDATE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to update origins."))

        try:
            event = Event.objects.get(catalog_id=catalog_id, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        try:
            origin = event.origins.get(id=origin_id)
        except Origin.DoesNotExist:
            raise NotFound(_("Origin not found."))

        serializer = OriginPayloadSerializer(
            origin, data=request.data, context={"request": request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OriginSerializer(origin).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Origin",
        operation_description=(
            """
            Delete an origin of an event in the catalog.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self,
        request: Request,
        organization_id: str,
        catalog_id: str,
        event_id: str,
        origin_id: str,
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(catalog_id, "catalog_id")
        self.validate_uuid(event_id, "event_id")
        self.validate_uuid(origin_id, "origin_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.DELETE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to delete origins."))

        try:
            event = Event.objects.get(catalog_id=catalog_id, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        try:
            origin = event.origins.get(id=origin_id)
        except Origin.DoesNotExist:
            raise NotFound(_("Origin not found."))

        origin.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
