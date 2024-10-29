from urllib.parse import unquote
from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.contrib.bma.bulletin.serializers import BulletinPayloadSerializer
from waveview.event.models import Event
from waveview.organization.permissions import PermissionType
from waveview.tasks.notify_event_observer import OperationType, notify_event_observer


class BMABulletinResponseSerializer(serializers.Serializer):
    message = serializers.CharField(
        help_text=_("Message indicating the operation status.")
    )


class BMABulletinEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="BMA Update Event",
        operation_description=(
            """
            Update event data from BMA bulletin. If the event does not exist, it
            will be created. This endpoint particularly used for syncing event
            data from existing BMA bulletin.
            """
        ),
        tags=["BMA"],
        request_body=BulletinPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", BMABulletinResponseSerializer),
        },
    )
    def put(
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
        event_id: str,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.CREATE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to create events."))

        event_id = unquote(event_id)
        bulletin = BulletinPayloadSerializer(
            data=request.data,
            context={
                "user": request.user,
                "catalog_id": catalog.id,
                "event_id": event_id,
            },
        )
        bulletin.is_valid(raise_exception=True)
        event: Event = bulletin.save()

        notify_event_observer.delay(
            OperationType.UPDATE, str(event.id), str(volcano.id)
        )

        return Response({"message": "Event updated."}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="BMA Delete Event",
        operation_description=(
            """
            Delete an event from the catalog. This endpoint particularly used for
            deleting event data from existing BMA bulletin.
            """
        ),
        tags=["BMA"],
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
        event_id: str,
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

        event_id = unquote(event_id)
        try:
            event = Event.objects.get(catalog=catalog, refid=event_id)
            event.delete()
        except Event.DoesNotExist:
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)
