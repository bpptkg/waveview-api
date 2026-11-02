from datetime import timedelta
from uuid import UUID

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.contrib.autoclass.task import preview_state, request_preview
from waveview.event.models import Event
from waveview.organization.permissions import PermissionType


class AutoclassPreviewPayloadSerializer(serializers.Serializer):
    time = serializers.DateTimeField(
        help_text=_("Draft event time. Not saved to the event.")
    )


class EventAutoclassPreviewEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_event(self, request, organization_id, volcano_id, catalog_id, event_id):
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
            return Event.objects.select_related("catalog__volcano").get(
                catalog=catalog, id=event_id
            )
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

    def validate_time(self, data):
        serializer = AutoclassPreviewPayloadSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        when = serializer.validated_data["time"]
        if when > timezone.now() + timedelta(minutes=5):
            raise ValidationError({"time": _("Time cannot be in the future.")})
        return when

    @swagger_auto_schema(
        operation_id="Start Autoclass Preview",
        operation_description=(
            """
            Start an autoclass prediction for a draft event time. The event is
            not modified. Poll the GET endpoint with the same time for the result.
            """
        ),
        tags=["Event"],
        request_body=AutoclassPreviewPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("Ready or unavailable"),
            status.HTTP_202_ACCEPTED: openapi.Response("Pending"),
        },
    )
    def post(
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
        event_id: UUID,
    ) -> Response:
        event = self.get_event(
            request, organization_id, volcano_id, catalog_id, event_id
        )
        when = self.validate_time(request.data)
        state = request_preview(event, when)
        code = (
            status.HTTP_202_ACCEPTED
            if state["state"] == "pending"
            else status.HTTP_200_OK
        )
        return Response(state, status=code)

    @swagger_auto_schema(
        operation_id="Get Autoclass Preview",
        operation_description=(
            """
            Read the autoclass preview result for a draft event time.
            """
        ),
        tags=["Event"],
        query_serializer=AutoclassPreviewPayloadSerializer,
        responses={status.HTTP_200_OK: openapi.Response("Preview state")},
    )
    def get(
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
        event_id: UUID,
    ) -> Response:
        event = self.get_event(
            request, organization_id, volcano_id, catalog_id, event_id
        )
        when = self.validate_time(request.query_params)
        return Response(preview_state(event, when), status=status.HTTP_200_OK)
