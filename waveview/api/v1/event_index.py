from django.db import models
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.pagination import StrictPageNumberPagination
from waveview.api.permissions import IsOrganizationMember
from waveview.event.models import Event, Origin
from waveview.event.serializers import EventPayloadSerializer, EventSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class OrderingType(models.TextChoices):
    ASC = "asc", _("Ascending")
    DESC = "desc", _("Descending")


class ParamSerializer(serializers.Serializer):
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    event_type_id = serializers.UUIDField(required=False)
    ordering = serializers.ChoiceField(
        required=False, choices=OrderingType.choices, default=OrderingType.DESC
    )


class EventIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    pagination_class = StrictPageNumberPagination

    @swagger_auto_schema(
        operation_id="List Events",
        operation_description=(
            """
            List events in the catalog.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", EventSerializer(many=True)),
        },
        manual_parameters=[
            openapi.Parameter(
                "start",
                openapi.IN_QUERY,
                description="Start date of the origin time of the event.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "end",
                openapi.IN_QUERY,
                description="End date of the origin time of the event",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "event_type_id",
                openapi.IN_QUERY,
                description="Event type ID.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Ordering of the events. Default is descending.",
                type=openapi.TYPE_STRING,
                enum=OrderingType.values,
            ),
        ],
    )
    def get(self, request: Request, organization_id: str, catalog_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(catalog_id, "catalog_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        events = (
            Event.objects.filter(catalog_id=catalog_id)
            .select_related("type")
            .prefetch_related("origins", "magnitudes", "amplitudes", "attachments")
        )

        param = ParamSerializer(data=request.query_params)
        param.is_valid(raise_exception=True)
        start = param.validated_data.get("start")
        end = param.validated_data.get("end")
        event_type_id = param.validated_data.get("event_type_id")
        ordering = param.validated_data.get("ordering")

        if start or end:
            origin_ids = Origin.objects.filter(
                **{"time__gte": start} if start else {},
                **{"time__lte": end} if end else {}
            ).values_list("id", flat=True)
            events = events.filter(origins__id__in=origin_ids)

        if event_type_id:
            events = events.filter(type_id=event_type_id)

        if ordering == OrderingType.ASC:
            events = events.order_by("origin__time")
        elif ordering == OrderingType.DESC:
            events = events.order_by("-origin__time")

        page = self.paginate_queryset(events.distinct())
        serializer = EventSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_id="Create Event",
        operation_description=(
            """
            Create a new event in the catalog.
            """
        ),
        tags=["Event"],
        request_body=EventPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", EventSerializer),
        },
    )
    def post(self, request: Request, organization_id: str, catalog_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(catalog_id, "catalog_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.CREATE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to create events."))

        serializer = EventPayloadSerializer(
            data=request.data, context={"request": request, "catalog_id": catalog_id}
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save(catalog_id=catalog_id, author=request.user)
        return Response(EventSerializer(event).data, status=status.HTTP_201_CREATED)
