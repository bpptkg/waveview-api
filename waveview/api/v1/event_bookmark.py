from uuid import UUID

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
from waveview.event.models import Event


class BookmarkEventSerializer(serializers.Serializer):
    event_id = serializers.UUIDField(help_text=_("Event ID."))
    is_bookmarked = serializers.BooleanField(help_text=_("True if bookmarked."))


class BookmarkEventEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Bookmark Event",
        operation_description=(
            """
            Bookmark or unbookmark an event in the catalog.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", BookmarkEventSerializer),
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

        try:
            event = Event.objects.get(catalog=catalog, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))

        user = request.user
        if event.bookmarked_by.filter(id=user.id).exists():
            event.bookmarked_by.remove(user)
            is_bookmarked = False
        else:
            event.bookmarked_by.add(user)
            is_bookmarked = True

        return Response(
            {"is_bookmarked": is_bookmarked, "event_id": event.id},
            status=status.HTTP_200_OK,
        )
