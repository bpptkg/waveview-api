from dataclasses import dataclass
from io import StringIO
from uuid import UUID

import pandas as pd
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
from waveview.api.serializers import CommaSeparatedListField
from waveview.event.models import Event, EventType
from waveview.organization.permissions import PermissionType


class ParamSerializer(serializers.Serializer):
    start = serializers.DateTimeField(
        required=True, help_text="Start date of the query in ISO 8601 format."
    )
    end = serializers.DateTimeField(
        required=True, help_text="End date of the query in ISO 8601 format."
    )
    event_types = CommaSeparatedListField(
        required=False, help_text="Event type codes to filter in comma separated list."
    )


@dataclass
class EventItem:
    id: UUID
    time: str
    duration: float
    type: str
    magnitude: float | None
    latitude: float | None
    longitude: float | None
    depth: float | None
    evaluation_mode: str | None
    evaluation_status: str | None
    author: str


COLUMNS = [
    "ID",
    "Time (UTC)",
    "Duration (s)",
    "Type",
    "Magnitude",
    "Latitude (°)",
    "Longitude (°)",
    "Depth (km)",
    "Evaluation Mode",
    "Evaluation Status",
    "Author",
]


class DownloadEventsEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Download Event",
        operation_description=(
            """
            Download event data for a given catalog and return CSV file. Only
            organization members with the given permission can access this
            endpoint.
            """
        ),
        tags=["Catalog"],
        responses={status.HTTP_200_OK: openapi.Response("OK")},
        query_serializer=ParamSerializer,
    )
    def get(
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

        serializer = ParamSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        start = serializer.validated_data["start"]
        end = serializer.validated_data["end"]
        event_types = serializer.validated_data.get("event_types")

        queryset = (
            Event.objects.select_related("type", "catalog")
            .prefetch_related("origins", "magnitudes", "amplitudes")
            .filter(catalog=catalog, time__gte=start, time__lte=end)
        )

        if event_types:
            types = EventType.objects.filter(
                organization=organization, code__in=event_types
            )
            queryset = queryset.filter(type__in=types)

        events: list[EventItem] = []
        for event in queryset.all():
            preferred_origin = event.preferred_origin()
            preferred_magnitude = event.preferred_magnitude()
            magnitude = preferred_magnitude.magnitude if preferred_magnitude else None
            latitude = preferred_origin.latitude if preferred_origin else None
            longitude = preferred_origin.longitude if preferred_origin else None
            depth = preferred_origin.depth if preferred_origin else None
            if event.author:
                author = event.author.name or event.author.username
            else:
                author = None
            item = EventItem(
                id=event.id,
                time=event.time.isoformat(),
                duration=event.duration,
                type=event.type.code,
                magnitude=magnitude,
                latitude=latitude,
                longitude=longitude,
                depth=depth,
                evaluation_mode=event.evaluation_mode,
                evaluation_status=event.evaluation_status,
                author=author,
            )
            events.append(item)

        df = pd.DataFrame(
            [
                [
                    item.id,
                    item.time,
                    item.duration,
                    item.type,
                    item.magnitude,
                    item.latitude,
                    item.longitude,
                    item.depth,
                    item.evaluation_mode,
                    item.evaluation_status,
                    item.author,
                ]
                for item in events
            ],
            columns=COLUMNS,
        )
        output = StringIO()
        df.to_csv(output, index=False)
        csv = output.getvalue()

        response = Response(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="events.csv"'
        response.write(csv)
        return response
