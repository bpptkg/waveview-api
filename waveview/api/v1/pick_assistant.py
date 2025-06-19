from uuid import UUID

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.contrib.pick_assistant import PickAssistant, PickAssistantInput


class PickAssistantPayloadSerializer(serializers.Serializer):
    t_onset = serializers.DateTimeField(help_text="Start time of the pick.")


class PickAssistantResponseSerializer(serializers.Serializer):
    start = serializers.DateTimeField(help_text="Start time of the pick.")
    end = serializers.DateTimeField(help_text="End time of the pick.")
    duration = serializers.FloatField(help_text="Duration of the pick in seconds.")
    stream_id = serializers.CharField(help_text="Stream ID associated with the pick.")
    channel_id = serializers.CharField(help_text="Channel ID associated with the pick.")


class PickAssistantEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Pick Assistant",
        operation_description=(
            """
            Use the pick assistant to generate picks based on the provided start
            time.
            """
        ),
        tags=["Signal"],
        request_body=PickAssistantPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", PickAssistantResponseSerializer),
        },
    )
    def post(
        self,
        request: Request,
        organization_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        serializer = PickAssistantPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        t_onset = serializer.validated_data["t_onset"]
        assistant = PickAssistant()
        input_data = PickAssistantInput(t_onset=t_onset)
        output_data = assistant.process(input_data)
        return Response(
            PickAssistantResponseSerializer(output_data).data, status=status.HTTP_200_OK
        )
