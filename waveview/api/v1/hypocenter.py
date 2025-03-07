from uuid import UUID

from django.db.models import F
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.api.serializers import CommaSeparatedListField
from waveview.appconfig.models import HypocenterConfig
from waveview.event.models import Event, EventType, Origin
from waveview.event.serializers import HypocenterSerializer


class QueryParamsSerializer(serializers.Serializer):
    start = serializers.DateTimeField(
        required=True, help_text="Start date of the query in ISO 8601 format."
    )
    end = serializers.DateTimeField(
        required=True, help_text="End date of the query in ISO 8601 format."
    )
    method = serializers.CharField(
        required=False, help_text="Filter origins by its method name."
    )
    event_types = CommaSeparatedListField(
        required=False,
        help_text="Event type codes to filter in comma separated list, e.g ``ROCKFALL,AWANPANAS``.",
    )


class HypocenterEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get Hypocenter",
        operation_description=(
            """
            Get hypocenter data for a given catalog.
            """
        ),
        tags=["Catalog"],
        responses={status.HTTP_200_OK: openapi.Response("OK", HypocenterSerializer)},
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
        method = params.validated_data.get("method")
        event_types = params.validated_data.get("event_types")

        queryset = (
            Event.objects.select_related("type", "catalog")
            .prefetch_related("origins", "magnitudes")
            .filter(catalog=catalog, time__gte=start, time__lte=end)
        )
        if method:
            origins = Origin.objects.filter(method__iexact=method)
            queryset = queryset.filter(origin__in=origins)

        if event_types:
            types = EventType.objects.filter(
                organization=organization, code__in=event_types
            )
        else:
            try:
                types = HypocenterConfig.objects.get(
                    volcano=volcano, is_preferred=True
                ).event_types.all()
            except HypocenterConfig.DoesNotExist:
                types = []

        hypocenters = (
            queryset.filter(type__in=types)
            .annotate(
                event_type=F("type__code"),
                origin_id=F("origin__id"),
                latitude=F("origin__latitude"),
                latitude_uncertainty=F("origin__latitude_uncertainty"),
                longitude=F("origin__longitude"),
                longitude_uncertainty=F("origin__longitude_uncertainty"),
                depth=F("origin__depth"),
                depth_uncertainty=F("origin__depth_uncertainty"),
                magnitude_value=F("magnitude__magnitude"),
                magnitude_type=F("magnitude__type"),
                origin_method=F("origin__method"),
            )
            .values(
                "id",
                "event_type",
                "time",
                "duration",
                "origin_id",
                "latitude",
                "latitude_uncertainty",
                "longitude",
                "longitude_uncertainty",
                "depth",
                "depth_uncertainty",
                "magnitude_value",
                "magnitude_type",
                "origin_method",
            )
        )
        methods = list(Origin.objects.values_list("method", flat=True).distinct())
        serializer = HypocenterSerializer(
            {
                "methods": methods,
                "hypocenters": hypocenters,
                "event_types": [t.code for t in types],
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
