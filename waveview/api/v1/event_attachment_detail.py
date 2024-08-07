from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOwnerOrReadOnly
from waveview.event.models import Attachment


class EventAttachmentDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    @swagger_auto_schema(
        operation_id="Delete Event Attachment",
        operation_description=(
            """
            Delete an attachment from the event. Only the attachment owner can
            delete the attachment.
            """
        ),
        tags=["Event"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(self, request: Request, attachment_id: UUID) -> Response:
        try:
            attachment = Attachment.objects.get(id=attachment_id)
        except Attachment.DoesNotExist:
            raise NotFound(_("Attachment not found."))

        self.check_object_permissions(request, attachment)

        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
