from typing import TypedDict
from uuid import UUID

from django.db import models
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncHour
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.api.serializers import CommaSeparatedListField
from waveview.event.models import Catalog, Event, EventType, SeismicityConfig
from waveview.event.serializers import (
    SeismicityGroupByDaySerializer,
    SeismicityGroupByHourSerializer,
)
from waveview.organization.models import Organization


class CountItem(TypedDict):
    timestamp: str
    count: int


class ResultItem(TypedDict):
    event_type: EventType
    data: list[CountItem]


class GroupByType(models.TextChoices):
    HOUR = "hour", _("Hour")
    DAY = "day", _("Day")


class ParamSerializer(serializers.Serializer):
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    group_by = serializers.ChoiceField(
        required=False, choices=GroupByType.choices, default=GroupByType.DAY
    )
    event_types = CommaSeparatedListField(required=False)


class SeismicityEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get Seismicity",
        operation_description=(
            """
            Seismicity endpoint to get seismicity data for the specified volcano
            and organization. Only members of the organization can view the
            seismicity.
            """
        ),
        tags=["Analytics"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", SeismicityGroupByDaySerializer),
        },
        manual_parameters=[
            openapi.Parameter(
                "start",
                openapi.IN_QUERY,
                description="Start date of the query.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
            ),
            openapi.Parameter(
                "end",
                openapi.IN_QUERY,
                description="End date of the query.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
            ),
            openapi.Parameter(
                "group_by",
                openapi.IN_QUERY,
                description="Group by type. Default is grouped per day.",
                type=openapi.TYPE_STRING,
                enum=[GroupByType.HOUR, GroupByType.DAY],
            ),
            openapi.Parameter(
                "event_types",
                openapi.IN_QUERY,
                description=(
                    "Event types to filter in comma separated list. "
                    "If not provided, default configuration will be used."
                ),
                type=openapi.TYPE_STRING,
            ),
        ],
    )
    def get(
        self, request: Request, organization_id: UUID, catalog_id: UUID
    ) -> Response:
        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            catalog = Catalog.objects.get(id=catalog_id)
        except Catalog.DoesNotExist:
            raise NotFound(_("Catalog not found."))

        params = ParamSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        start = params.validated_data.get("start")
        end = params.validated_data.get("end")
        group_by = params.validated_data.get("group_by")
        event_types = params.validated_data.get("event_types")

        if event_types:
            types = EventType.objects.filter(
                organization=organization, code__in=event_types
            )
        else:
            type_ids = (
                SeismicityConfig.objects.filter(organization=organization)
                .order_by("order")
                .values_list("type", flat=True)
            )
            types = EventType.objects.filter(id__in=type_ids)

        result: list[ResultItem] = []

        for event_type in types:
            queryset = Event.objects.filter(
                catalog=catalog,
                time__gte=start,
                time__lte=end,
                type=event_type,
            )
            if group_by == GroupByType.HOUR:
                seismicity = (
                    queryset.annotate(timestamp=TruncHour("time"))
                    .values("timestamp")
                    .annotate(count=Count("id"))
                ).order_by("timestamp")
            elif group_by == GroupByType.DAY:
                seismicity = (
                    queryset.annotate(timestamp=TruncDay("time"))
                    .values("timestamp")
                    .annotate(count=Count("id"))
                ).order_by("timestamp")

            result.append({"event_type": event_type, "data": list(seismicity)})

        if group_by == GroupByType.HOUR:
            serializer = SeismicityGroupByHourSerializer(
                result, many=True, context={"request": request}
            )
        elif group_by == GroupByType.DAY:
            serializer = SeismicityGroupByDaySerializer(
                result, many=True, context={"request": request}
            )
        else:
            raise ValueError("Invalid group by type.")
        return Response(serializer.data, status=status.HTTP_200_OK)
