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
from waveview.observation.models import PyroclasticFlow, Rockfall


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
            falldirection=F("fall_direction__name"),
            rf=Value(1, models.IntegerField()),
            ap=Value(0, models.IntegerField()),
            rf_distance=F("runout_distance"),
            ap_distance=Value(0, models.FloatField()),
            distance=F("runout_distance"),
            azimuth=F("fall_direction__azimuth"),
        )
        ap_events = PyroclasticFlow.objects.filter(event__in=events).annotate(
            eventtime=F("event__time"),
            falldirection=F("fall_direction__name"),
            rf=Value(0, models.IntegerField()),
            ap=Value(1, models.IntegerField()),
            rf_distance=Value(0, models.FloatField()),
            ap_distance=F("runout_distance"),
            distance=F("runout_distance"),
            azimuth=F("fall_direction__azimuth"),
        )
        columns = [
            "eventtime",
            "falldirection",
            "rf",
            "ap",
            "rf_distance",
            "ap_distance",
            "distance",
            "azimuth",
        ]
        rf = rf_events.values(*columns)
        ap = ap_events.values(*columns)
        items = list(rf) + list(ap)

        df = pd.DataFrame(items)
        if df.empty:
            serializer = RfApDirectionSerializer(
                {"daily_results": [], "directional_results": []}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        df["eventtime"] = pd.to_datetime(df["eventtime"])

        dft = df.groupby(pd.Grouper(key="eventtime", freq="D")).agg(
            count=("eventtime", "count"),
            distance=("distance", "max"),
            rf_count=("rf", "sum"),
            ap_count=("ap", "sum"),
            rf_distance=("rf_distance", "max"),
            ap_distance=("ap_distance", "max"),
        )
        dft["time"] = dft.index.date
        dft.dropna(inplace=True, axis=0, how="any")
        results = dft.to_dict(orient="records")

        dfd = (
            df.groupby(
                [pd.Grouper(key="eventtime", freq="D"), "falldirection", "azimuth"]
            )
            .agg(
                count=("eventtime", "count"),
                distance=("distance", "max"),
                rf_count=("rf", "sum"),
                ap_count=("ap", "sum"),
                rf_distance=("rf_distance", "max"),
                ap_distance=("ap_distance", "max"),
            )
            .reset_index()
        )
        dfd["time"] = dfd["eventtime"].dt.date
        dfd.dropna(inplace=True, axis=0, how="any")
        directions = []
        for direction, group in dfd.groupby("falldirection"):
            data = (
                group[
                    [
                        "time",
                        "count",
                        "distance",
                        "rf_count",
                        "ap_count",
                        "rf_distance",
                        "ap_distance",
                    ]
                ]
                .dropna(axis=0, how="any")
                .to_dict(orient="records")
            )
            directions.append(
                {
                    "direction": direction,
                    "azimuth": group["azimuth"].iloc[0],
                    "count": group["count"].sum(),
                    "distance": group["distance"].max(),
                    "rf_count": group["rf_count"].sum(),
                    "ap_count": group["ap_count"].sum(),
                    "rf_distance": group["rf_distance"].max(),
                    "ap_distance": group["ap_distance"].max(),
                    "data": data,
                }
            )

        serializer = RfApDirectionSerializer(
            {"daily_results": results, "directional_results": directions}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
