from datetime import datetime, timedelta
from typing import TypedDict
from uuid import UUID

import pandas as pd
from django.db import models
from django.db.models import F, Value
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.event.header import ObservationType
from waveview.event.models import Event, EventType
from waveview.observation.models import FallDirection, PyroclasticFlow, Rockfall


class QueryParamsSerializer(serializers.Serializer):
    start = serializers.DateTimeField(help_text="Start date of the query.")
    end = serializers.DateTimeField(help_text="End date of the query.")


class ResultSerializer(serializers.Serializer):
    time = serializers.DateField(help_text="Day of the event")
    count = serializers.IntegerField(
        help_text="Number of Rockfall and Awan Panas events."
    )
    distance = serializers.FloatField(
        help_text="Maximum runout distance of Rockfall and Awan Panas events."
    )
    rf_count = serializers.IntegerField(help_text="Number of Rockfall events.")
    ap_count = serializers.IntegerField(help_text="Number of Awan Panas events.")
    rf_distance = serializers.FloatField(
        help_text="Maximum runout distance of Rockfall events."
    )
    ap_distance = serializers.FloatField(
        help_text="Maximum runout distance of Awan Panas events."
    )


class DirectionItemSerializer(serializers.Serializer):
    time = serializers.DateField(help_text="Day of the event.")
    rf_count = serializers.IntegerField(help_text="Number of Rockfall events.")
    ap_count = serializers.IntegerField(help_text="Number of Awan Panas events.")
    rf_distance = serializers.FloatField(
        help_text="Maximum runout distance of Rockfall events."
    )
    ap_distance = serializers.FloatField(
        help_text="Maximum runout distance of Awan Panas events."
    )
    count = serializers.IntegerField(help_text="Number of events.")
    distance = serializers.FloatField(help_text="Maximum runout distance of events.")


class DirectionSerializer(serializers.Serializer):
    direction = serializers.CharField(help_text="Fall direction of the event.")
    azimuth = serializers.FloatField(help_text="Azimuth of the fall direction.")
    count = serializers.IntegerField(
        help_text="Number of events with the fall direction."
    )
    distance = serializers.FloatField(
        help_text="Maximum runout distance of events with the fall direction."
    )
    rf_count = serializers.IntegerField(
        help_text="Number of Rockfall events with the fall direction."
    )
    ap_count = serializers.IntegerField(
        help_text="Number of Awan Panas events with the fall direction."
    )
    rf_distance = serializers.FloatField(
        help_text="Maximum runout distance of Rockfall events with the fall direction."
    )
    ap_distance = serializers.FloatField(
        help_text="Maximum runout distance of Awan Panas events with the fall direction."
    )
    data = DirectionItemSerializer(
        many=True, help_text="List of count and distance info grouped per day."
    )


class RfApDirectionSerializer(serializers.Serializer):
    daily_results = ResultSerializer(
        many=True, help_text="List of count and distance info grouped per day."
    )
    directional_results = DirectionSerializer(
        many=True, help_text="List of count and distance info grouped per direction."
    )


class DirectionDataItem(TypedDict):
    time: datetime
    count: int
    distance: float
    rf_count: int
    ap_count: int
    rf_distance: float
    ap_distance: float


class DirectionalResultDataItem(TypedDict):
    direction: str
    azimuth: float
    count: int
    distance: float
    rf_count: int
    ap_count: int
    rf_distance: float
    ap_distance: float
    data: list[DirectionDataItem]


def fills_data_gaps(
    data: list[DirectionDataItem], starttime: datetime, endtime: datetime
) -> list[DirectionDataItem]:
    if len(data) == 0:
        return []
    start = starttime.date()
    end = endtime.date()
    step = timedelta(days=1)

    new_index = pd.date_range(start=start, end=end, freq=step).date
    df = pd.DataFrame(data)
    df.set_index("time", inplace=True)
    df = df.reindex(new_index, fill_value=0)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "time"}, inplace=True)
    return df.to_dict(orient="records")


class RfApDirectionEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get RF & AP Direction",
        operation_description=(
            """
            Get the list of Rockfall and Awan Panas events grouped by fall
            direction.
            """
        ),
        tags=["Catalog"],
        query_serializer=QueryParamsSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", RfApDirectionSerializer()),
        },
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
        start = params.validated_data["start"]
        end = params.validated_data["end"]

        events = Event.objects.prefetch_related(
            "rockfall",
            "pyroclastic_flow",
        ).filter(
            catalog=catalog,
            time__gte=start,
            time__lt=end,
            type__in=EventType.objects.filter(
                observation_type__in=[
                    ObservationType.ROCKFALL,
                    ObservationType.PYROCLASTIC_FLOW,
                ]
            ),
        )

        rf_events = Rockfall.objects.filter(event__in=events).annotate(
            eventtime=F("event__time"),
            rf=Value(1, models.IntegerField()),
            ap=Value(0, models.IntegerField()),
            rf_distance=F("runout_distance"),
            ap_distance=Value(0, models.FloatField()),
            distance=F("runout_distance"),
        )
        ap_events = PyroclasticFlow.objects.filter(event__in=events).annotate(
            eventtime=F("event__time"),
            falldirection=F("fall_direction__name"),
            rf=Value(0, models.IntegerField()),
            ap=Value(1, models.IntegerField()),
            rf_distance=Value(0, models.FloatField()),
            ap_distance=F("runout_distance"),
            distance=F("runout_distance"),
        )
        columns = [
            "eventtime",
            "rf",
            "ap",
            "rf_distance",
            "ap_distance",
            "distance",
        ]
        items = list(rf_events.values(*columns)) + list(ap_events.values(*columns))

        daily_results: list[DirectionDataItem] = []
        dft = pd.DataFrame(items)
        if not dft.empty:
            dft["eventtime"] = pd.to_datetime(dft["eventtime"])
            df_time = dft.groupby(pd.Grouper(key="eventtime", freq="D")).agg(
                count=("eventtime", "count"),
                distance=("distance", "max"),
                rf_count=("rf", "sum"),
                ap_count=("ap", "sum"),
                rf_distance=("rf_distance", "max"),
                ap_distance=("ap_distance", "max"),
            )
            df_time["time"] = df_time.index.date
            df_time.dropna(inplace=True, axis=0, how="any")
            daily_results = df_time.to_dict(orient="records")

        directional_results: list[DirectionalResultDataItem] = []
        for direction in FallDirection.objects.all():
            rf = rf_events.filter(fall_directions=direction)
            ap = ap_events.filter(fall_directions=direction)
            items = list(rf.values(*columns)) + list(ap.values(*columns))
            dfd = pd.DataFrame(items)
            if dfd.empty:
                continue
            dfd["eventtime"] = pd.to_datetime(dfd["eventtime"])
            df_dir = dfd.groupby(pd.Grouper(key="eventtime", freq="D")).agg(
                count=("eventtime", "count"),
                distance=("distance", "max"),
                rf_count=("rf", "sum"),
                ap_count=("ap", "sum"),
                rf_distance=("rf_distance", "max"),
                ap_distance=("ap_distance", "max"),
            )
            df_dir["time"] = df_dir.index.date
            df_dir.dropna(inplace=True, axis=0, how="any")
            data = df_dir.to_dict(orient="records")
            directional_results.append(
                {
                    "direction": direction.name,
                    "azimuth": direction.azimuth,
                    "count": df_dir["count"].sum(),
                    "distance": df_dir["distance"].max(),
                    "rf_count": df_dir["rf_count"].sum(),
                    "ap_count": df_dir["ap_count"].sum(),
                    "rf_distance": df_dir["rf_distance"].max(),
                    "ap_distance": df_dir["ap_distance"].max(),
                    "data": fills_data_gaps(data, start, end),
                }
            )

        serializer = RfApDirectionSerializer(
            {"daily_results": daily_results, "directional_results": directional_results}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
