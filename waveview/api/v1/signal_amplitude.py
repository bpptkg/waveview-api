import concurrent.futures
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
from waveview.appconfig.models import PickerConfig
from waveview.appconfig.models.picker import PickerConfigData
from waveview.event.amplitude import SignalAmplitude, amplitude_registry


class SignalAmplitudePayloadSerializer(serializers.Serializer):
    time = serializers.DateTimeField(help_text=_("The time of the event."))
    duration = serializers.FloatField(help_text=_("The duration of the event."))


class SignalAmplitudeSerializer(serializers.Serializer):
    stream_id = serializers.CharField(help_text=_("The stream ID of the event."))
    amplitude = serializers.FloatField(help_text=_("The amplitude of the event."))
    unit = serializers.CharField(help_text=_("The unit of the amplitude."))
    method = serializers.CharField(
        help_text=_("The method used to calculate the amplitude.")
    )
    category = serializers.CharField(help_text=_("The category of the amplitude."))
    time = serializers.DateTimeField(help_text=_("The time of the event."))
    duration = serializers.FloatField(help_text=_("The duration of the event."))


class SignalAmplitudeEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Calculate Signal Amplitude",
        operation_description=(
            """
            This endpoint allows users to calculate the signal amplitude of an event.
            """
        ),
        tags=["Amplitude"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", SignalAmplitudeSerializer(many=True)
            ),
        },
    )
    def post(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)

        try:
            config = PickerConfig.objects.filter(
                organization=organization, volcano=volcano
            ).get()
        except PickerConfig.DoesNotExist:
            raise NotFound(_("Picker config not found."))

        serializer = SignalAmplitudePayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        time = serializer.validated_data["time"]
        duration = serializer.validated_data["duration"]

        data = PickerConfigData.from_dict(config.data)
        method = data.amplitude_config.amplitude_calculator
        calculator = amplitude_registry.get(method)
        if calculator is None:
            raise NotFound(_("Amplitude calculator not found."))

        amplitudes: list[SignalAmplitude] = []

        def calculate_amplitude(channel_id: str) -> SignalAmplitude:
            return calculator.calc(time, duration, channel_id, organization_id)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(calculate_amplitude, channel.channel_id)
                for channel in data.amplitude_config.channels
            ]
            for future in concurrent.futures.as_completed(futures):
                ampl = future.result()
                amplitudes.append(ampl)

        return Response(
            SignalAmplitudeSerializer(
                sorted(amplitudes, key=lambda x: x.amplitude, reverse=True), many=True
            ).data,
            status=status.HTTP_200_OK,
        )
