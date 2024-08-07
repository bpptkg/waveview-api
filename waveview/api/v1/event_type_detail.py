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
from waveview.event.models import EventType
from waveview.event.serializers import EventTypePayloadSerializer, EventTypeSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class EventTypeDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Event Type",
        operation_description=(
            """
            Retrieve an event type within the organization. Only users within
            the organization can view the event type.
            """
        ),
        tags=["Event Type"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", EventTypeSerializer),
        },
    )
    def get(
        self, request: Request, organization_id: UUID, event_type_id: UUID
    ) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            event_type = EventType.objects.get(
                organization_id=organization_id, id=event_type_id
            )
        except EventType.DoesNotExist:
            raise NotFound(_("Event type not found."))

        serializer = EventTypeSerializer(event_type)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Event Type",
        operation_description=(
            """
            Update an event type within the organization. Only authorized users
            can update event types.
            """
        ),
        tags=["Event Type"],
        request_body=EventTypePayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", EventTypeSerializer),
        },
    )
    def put(
        self, request: Request, organization_id: UUID, event_type_id: UUID
    ) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            event_type = EventType.objects.get(
                organization_id=organization_id, id=event_type_id
            )
        except EventType.DoesNotExist:
            raise NotFound(_("Event type not found."))

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_EVENT_TYPE
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to update event types.")
            )

        serializer = EventTypePayloadSerializer(
            instance=event_type,
            data=request.data,
            context={"request": request, "organization_id": organization_id},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(EventTypeSerializer(event_type).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Event Type",
        operation_description=(
            """
            Delete an event type within the organization. Only organization owner
            can delete event types.
            """
        ),
        tags=["Event Type"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self, request: Request, organization_id: UUID, event_type_id: UUID
    ) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            event_type = EventType.objects.get(
                organization_id=organization_id, id=event_type_id
            )
        except EventType.DoesNotExist:
            raise NotFound(_("Event type not found."))

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_EVENT_TYPE
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to delete event types.")
            )

        event_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
