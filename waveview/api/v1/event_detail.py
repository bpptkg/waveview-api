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
from waveview.event.models import Event
from waveview.event.serializers import EventDetailSerializer, EventPayloadSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class EventDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Event",
        operation_description=(
            """
            Retrieve an event in the catalog.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", EventDetailSerializer),
        },
    )
    def get(
        self, request: Request, organization_id: UUID, catalog_id: UUID, event_id: UUID
    ) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            event = Event.objects.get(catalog_id=catalog_id, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        serializer = EventDetailSerializer(event, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Event",
        operation_description=(
            """
            Update an event in the catalog.
            """
        ),
        tags=["Event"],
        request_body=EventPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", EventDetailSerializer),
        },
    )
    def put(
        self, request: Request, organization_id: UUID, catalog_id: UUID, event_id: UUID
    ) -> Response:
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
            raise PermissionDenied(_("You do not have permission to update events."))

        try:
            event = Event.objects.get(catalog_id=catalog_id, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        serializer = EventPayloadSerializer(
            event, data=request.data, context={"request": request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        return Response(
            EventDetailSerializer(event, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        operation_id="Delete Event",
        operation_description=(
            """
            Delete an event in the catalog.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self, request: Request, organization_id: UUID, catalog_id: UUID, event_id: UUID
    ) -> Response:
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
            raise PermissionDenied(_("You do not have permission to delete events."))

        try:
            event = Event.objects.get(catalog_id=catalog_id, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
