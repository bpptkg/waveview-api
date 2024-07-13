from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.event.serializers import (
    AttachmentPayloadSchema,
    AttachmentPayloadSerializer,
    AttachmentSerializer,
)


class EventAttachmentUploadEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="Upload Event Attachment",
        operation_description=(
            """
            Upload an attachment to the event. Any user can upload attachments.
            """
        ),
        tags=["Event"],
        request_body=AttachmentPayloadSchema,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", AttachmentSerializer),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = AttachmentPayloadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save()
        return Response(
            AttachmentSerializer(attachment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
