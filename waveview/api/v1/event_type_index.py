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


class EventTypeIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Event Types",
        operation_description=(
            """
            List all event types within the organization. Only users within the
            organization can view the event types.
            """
        ),
        tags=["Event Type"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", EventTypeSerializer(many=True)),
        },
    )
    def get(self, request: Request, organization_id: UUID) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        event_types = EventType.objects.filter(organization_id=organization_id)
        serializer = EventTypeSerializer(event_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Event Type",
        operation_description=(
            """
            Create a new event type within the organization. Only authorized
            users can create event types.
            """
        ),
        tags=["Event Type"],
        request_body=EventTypePayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", EventTypeSerializer),
        },
    )
    def post(self, request: Request, organization_id: UUID) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_EVENT_TYPE
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to create event types.")
            )

        serializer = EventTypePayloadSerializer(
            data=request.data,
            context={"request": request, "organization_id": organization_id},
        )
        serializer.is_valid(raise_exception=True)
        event_type = serializer.save()
        return Response(
            EventTypeSerializer(event_type).data, status=status.HTTP_201_CREATED
        )
