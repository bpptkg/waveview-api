from datetime import datetime, timedelta
from typing import TypedDict
from uuid import UUID

import pandas as pd
from django.db import models
from django.db.models import Case, Count, When
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
from waveview.appconfig.models import SeismicityConfig
from waveview.event.models import Event, EventType
from waveview.event.serializers import (
    SeismicityGroupByDaySerializer,
    SeismicityGroupByHourSerializer,
)


class CountItem(TypedDict):
    timestamp: datetime
    count: int


class ResultItem(TypedDict):
    event_type: EventType
    data: list[CountItem]


class GroupByType(models.TextChoices):
    HOUR = "hour", _("Hour")
    DAY = "day", _("Day")


class QueryParamsSerializer(serializers.Serializer):
    start = serializers.DateTimeField(
        required=True, help_text="Start date of the query."
    )
    end = serializers.DateTimeField(required=True, help_text="End date of the query.")
    group_by = serializers.ChoiceField(
        required=False,
        choices=GroupByType.choices,
        default=GroupByType.DAY,
        help_text="Group by type. Default is grouped per day.",
    )
    event_types = CommaSeparatedListField(
        required=False, help_text="Event type codes to filter in comma separated list."
    )
    fill_gaps = serializers.BooleanField(
        required=False, default=False, help_text="Whether to fill the gaps in the data."
    )


def fill_data_gaps(
    data: list[CountItem], start: datetime, end: datetime, group_by: str
) -> list[CountItem]:
    if group_by == GroupByType.HOUR:
        start = start.replace(minute=0, second=0, microsecond=0)
        end = end.replace(minute=0, second=0, microsecond=0)
        step = timedelta(hours=1)
    elif group_by == GroupByType.DAY:
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(hour=0, minute=0, second=0, microsecond=0)
        step = timedelta(days=1)
    else:
        raise ValueError("Invalid group by type.")

    new_index = pd.date_range(start=start, end=end, freq=step)
    if len(data) == 0:
        df = pd.DataFrame(columns=["timestamp", "count"])
    else:
        df = pd.DataFrame(data)

    df.set_index("timestamp", inplace=True)
    df = df.reindex(new_index, fill_value=0)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "timestamp"}, inplace=True)
    return df.to_dict(orient="records")


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
        tags=["Catalog"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", SeismicityGroupByDaySerializer(many=True)
            ),
        },
        query_serializer=QueryParamsSerializer,
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

        params = QueryParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        start = params.validated_data.get("start")
        end = params.validated_data.get("end")
        group_by = params.validated_data.get("group_by")
        event_types = params.validated_data.get("event_types")
        fill_gaps = params.validated_data.get("fill_gaps")

        if event_types:
            types = EventType.objects.filter(
                organization=organization, code__in=event_types
            )
        else:
            type_ids = (
                SeismicityConfig.objects.filter(volcano=volcano)
                .order_by("order")
                .values_list("type", flat=True)
            )
            if not type_ids:
                types = []
            else:
                order_conditions = [
                    When(id=type_id, then=pos) for pos, type_id in enumerate(type_ids)
                ]
                types = EventType.objects.filter(id__in=type_ids).order_by(
                    Case(*order_conditions)
                )

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

            if fill_gaps:
                data = fill_data_gaps(
                    [
                        {"timestamp": item["timestamp"], "count": item["count"]}
                        for item in seismicity
                    ],
                    start,
                    end,
                    group_by,
                )
            else:
                data = list(seismicity)

            result.append({"event_type": event_type, "data": data})

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
