from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.event.models import Event
from waveview.observation.models import PyroclasticFlow
from waveview.tasks.send_wa_notification import send_wa_notification


class SendToWAPayloadSerializer(serializers.Serializer):
    event_id = serializers.UUIDField(help_text="The ID of the event to send to WA.")


class SendToWAResponseSerializer(serializers.Serializer):
    message = serializers.CharField(
        help_text="A message indicating the result of the operation."
    )


class SendToWAEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Send Event to WA",
        operation_description=("""
            This endpoint allows users to send a Pyroclastic Flow event to
            WhatsApp for notification purposes.
            """),
        tags=["Event"],
        request_body=SendToWAPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", SendToWAResponseSerializer),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = SendToWAPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event_id = serializer.validated_data["event_id"]

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError(
                f"Event with ID {event_id} does not exist."
            )
        try:
            PyroclasticFlow.objects.get(event=event)
        except PyroclasticFlow.DoesNotExist:
            raise serializers.ValidationError(
                f"No Pyroclastic Flow observation found for event ID {event_id}."
            )

        send_wa_notification(str(event_id))

        return Response(
            {"message": f"Event {event_id} has been sent to WA."}
        )
