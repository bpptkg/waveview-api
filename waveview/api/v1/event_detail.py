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
from waveview.event.observers import OperationType
from waveview.event.serializers import EventDetailSerializer, EventPayloadSerializer
from waveview.notifications.types import NotifyEventData
from waveview.organization.permissions import PermissionType
from waveview.tasks.notify_event import notify_event
from waveview.tasks.notify_event_observer import OperationType, notify_event_observer


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
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
        event_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        try:
            event = Event.objects.get(catalog=catalog, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        serializer = EventDetailSerializer(event)
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
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
        event_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.UPDATE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to update events."))

        try:
            event = Event.objects.get(catalog=catalog, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        serializer = EventPayloadSerializer(
            event, data=request.data, context={"request": request}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save()

        notify_event_observer.delay(
            OperationType.UPDATE, str(event.id), str(volcano.id)
        )

        payload = NotifyEventData.from_event(
            str(request.user.id), str(organization.id), event
        )
        notify_event.delay(OperationType.UPDATE, payload.to_dict())

        return Response(
            EventDetailSerializer(event).data,
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
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
        event_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.DELETE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to delete events."))

        try:
            event = Event.objects.get(catalog=catalog, id=event_id)
            refid = event.refid
            payload = NotifyEventData.from_event(
                str(request.user.id), str(organization.id), event
            )
            event.delete()
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        notify_event_observer.delay(
            OperationType.DELETE, str(event_id), str(volcano.id), refid=refid
        )
        notify_event.delay(OperationType.DELETE, payload.to_dict())

        return Response(status=status.HTTP_204_NO_CONTENT)
