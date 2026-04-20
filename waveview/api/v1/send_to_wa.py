from zoneinfo import ZoneInfo

import requests
from django.conf import settings
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
from waveview.whatsapp.models import Group


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
        operation_description=(
            """
            This endpoint allows users to send a Pyroclastic Flow event to
            WhatsApp for notification purposes.
            """
        ),
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
            pf = PyroclasticFlow.objects.get(event=event)
        except PyroclasticFlow.DoesNotExist:
            raise serializers.ValidationError(
                f"No Pyroclastic Flow observation found for event ID {event_id}."
            )

        groups = Group.objects.filter(excluded=False)
        url = "https://broadcast-api.cendana15.com/messages"
        headers = {
            "Authorization": f"Bearer {settings.BROADCAST_TOKEN}",
            "Content-Type": "application/json",
        }
        event_time_wib = event.time.astimezone(ZoneInfo("Asia/Jakarta"))
        final_message = (
            f"*Info APG:*\n"
            f"Tanggal: {event_time_wib.strftime('%d %B %Y')}\n"
            f"Jam: {event_time_wib.strftime('%H.%M.%S')} WIB\n"
            f"Durasi: {(event.duration)} detik\n"
            f"Amplitudo maks: {(pf.amplitude)} mm\n"
            f"Estimasi jarak luncur: {(pf.runout_distance)} m\n"
            f"Arah: {', '.join([fd.name for fd in pf.fall_directions.all()])}"
        )
        if settings.BROADCAST_TESTING:
            final_message = "[TESTING]\n" + final_message
        body = {
            "type": "Group",
            "is_wa": 1,
            "is_sms": 0,
            "message": final_message,
            "receiver": [
                {"id": group.group_id, "name": group.name} for group in groups
            ],
        }

        response = requests.post(url, json=body, headers=headers)
        if response.status_code != 200:
            raise serializers.ValidationError(
                f"Failed to send message to WA. Status code: {response.status_code}, Response: {response.text}"
            )

        return Response(
            {"message": f"Event {event_id} has been sent to WA successfully."}
        )
