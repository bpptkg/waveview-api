from uuid import UUID

from django.db import models
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.pagination import FlexiblePageNumberPagination
from waveview.api.permissions import IsOrganizationMember
from waveview.api.serializers import CommaSeparatedListField
from waveview.event.models import Event
from waveview.event.observers import OperationType
from waveview.event.serializers import (
    EventDetailSerializer,
    EventPayloadSerializer,
    EventSerializer,
)
from waveview.notifications.types import NotifyEventData
from waveview.organization.permissions import PermissionType
from waveview.tasks.notify_event import notify_event
from waveview.tasks.notify_event_observer import notify_event_observer


class OrderingType(models.TextChoices):
    ASC = "asc", _("Ascending")
    DESC = "desc", _("Descending")


class ParamSerializer(serializers.Serializer):
    start = serializers.DateTimeField(
        required=False, help_text="Start date of the event."
    )
    end = serializers.DateTimeField(required=False, help_text="End date of the event.")
    event_types = CommaSeparatedListField(
        required=False, help_text="Event type codes to filter in comma separated list."
    )
    ordering = serializers.ChoiceField(
        required=False,
        choices=OrderingType.choices,
        default=OrderingType.DESC,
        help_text="Ordering of the events.",
    )
    is_bookmarked = serializers.BooleanField(
        required=False, help_text="Filter events that are bookmarked by the user."
    )


class EventIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]
    pagination_class = FlexiblePageNumberPagination

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

        param = ParamSerializer(data=request.query_params)
        param.is_valid(raise_exception=True)
        start = param.validated_data.get("start")
        end = param.validated_data.get("end")
        event_types = param.validated_data.get("event_types")
        ordering = param.validated_data.get("ordering")
        is_bookmarked = param.validated_data.get("is_bookmarked")

        events = (
            Event.objects.filter(catalog=catalog)
            .select_related("type")
            .prefetch_related("origins", "magnitudes", "amplitudes", "attachments")
        )

        if start:
            events = events.filter(time__gte=start)
        if end:
            events = events.filter(time__lte=end)

        if event_types:
            events = events.filter(type__code__in=event_types)

        if is_bookmarked:
            events = events.filter(bookmarked_by=request.user)

        if ordering == OrderingType.ASC:
            events = events.order_by("time")
        elif ordering == OrderingType.DESC:
            events = events.order_by("-time")

        page = self.paginate_queryset(events)
        if page is not None:
            serializer = EventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            organization_id, PermissionType.CREATE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to create events."))

        serializer = EventPayloadSerializer(
            data=request.data, context={"request": request, "catalog_id": catalog.id}
        )
        serializer.is_valid(raise_exception=True)
        event = serializer.save()
        use_outlier_filter = serializer.validated_data.get("use_outlier_filter", False)

        notify_event_observer.delay(
            OperationType.CREATE,
            str(event.id),
            str(volcano.id),
            use_outlier_filter=use_outlier_filter,
        )

        payload = NotifyEventData.from_event(
            str(request.user.id), str(organization.id), event
        )
        notify_event.delay(OperationType.CREATE, payload.to_dict())

        return Response(
            EventDetailSerializer(event).data,
            status=status.HTTP_201_CREATED,
        )
