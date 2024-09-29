from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.event.models import Event
from waveview.event.serializers import OriginPayloadSerializer, OriginSerializer
from waveview.organization.permissions import PermissionType


class EventOriginIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Origins",
        operation_description=(
            """
            List origins of an event in the catalog.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", OriginSerializer(many=True)),
        },
    )
    def get(
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
        event_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        try:
            event = Event.objects.get(catalog=catalog, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        serializer = OriginSerializer(event.origins.order_by("time"), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Origin",
        operation_description=(
            """
            Create an origin for an event in the catalog.
            """
        ),
        tags=["Event"],
        request_body=OriginPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", OriginSerializer),
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
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.CREATE_EVENT
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to create origins."))

        try:
            event = Event.objects.get(catalog=catalog, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        serializer = OriginPayloadSerializer(
            data=request.data, context={"request": request, "event_id": event.id}
        )
        serializer.is_valid(raise_exception=True)
        origin = serializer.save()
        return Response(OriginSerializer(origin).data, status=status.HTTP_201_CREATED)
