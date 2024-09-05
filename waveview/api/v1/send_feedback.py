from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.feedback.serializers import FeedbackPayloadSerializer


class SendFeedbackSerializer(serializers.Serializer):
    message = serializers.CharField(help_text=_("Feedback message"))


class SendFeedbackEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="Send Feedback",
        operation_description=(
            """
            Send feedback to the system administrators.
            """
        ),
        tags=["Feedback"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", SendFeedbackSerializer()),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = FeedbackPayloadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        msg = _("Feedback sent successfully.")
        return Response({"message": msg}, status=status.HTTP_200_OK)
