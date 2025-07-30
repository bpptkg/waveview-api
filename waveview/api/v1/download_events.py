from datetime import timedelta
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
from waveview.event.models import Event, EventType
from waveview.event.serializers import EventDetailSerializer
from waveview.organization.permissions import PermissionType


class DownloadEventsPayloadSerializer(serializers.Serializer):
    date = serializers.DateTimeField(
        required=True, help_text="Date of the query in ISO 8601 format."
    )
    event_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Event type codes to filter.",
    )


class DownloadEventsEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Download Events",
        operation_description=(
            """
            Download event data for a given catalog and return JSON file. Only
            organization members with the given permission can access this
            endpoint.
            """
        ),
        tags=["Catalog"],
        request_body=DownloadEventsPayloadSerializer,
        responses={status.HTTP_200_OK: openapi.Response("OK")},
    )
    def post(
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.DOWNLOAD_EVENT
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to download event data.")
            )

        serializer = DownloadEventsPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start = serializer.validated_data["date"]
        event_types = serializer.validated_data.get("event_types")
        end = start + timedelta(days=1)

        queryset = (
            Event.objects.select_related("type", "catalog")
            .prefetch_related("origins", "magnitudes", "amplitudes")
            .filter(catalog=catalog, time__gte=start, time__lt=end)
        )

        if event_types:
            types = EventType.objects.filter(
                organization=organization, code__in=event_types
            )
            queryset = queryset.filter(type__in=types)

        serializer = EventDetailSerializer(
            queryset, many=True, context={"request": request}
        )
        data = serializer.data
        response = Response(data, content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="events.json"'
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response
