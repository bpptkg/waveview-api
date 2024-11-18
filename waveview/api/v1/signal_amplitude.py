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
from waveview.appconfig.models.picker import ChannelConfigData, PickerConfigData
from waveview.event.amplitude import SignalAmplitude, amplitude_registry
from waveview.event.header import AmplitudeCategory, AmplitudeUnit


class SignalAmplitudePayloadSerializer(serializers.Serializer):
    time = serializers.DateTimeField(help_text=_("The time of the event."))
    duration = serializers.FloatField(help_text=_("The duration of the event."))
    use_outlier_filter = serializers.BooleanField(
        help_text=_("Whether to use a outlier filter to smooth the signal."),
        default=False,
    )


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
    label = serializers.CharField(
        help_text=_("The label of the event."), required=False, allow_null=True
    )


class SignalAmplitudeEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Calculate Signal Amplitude",
        operation_description=(
            """
            This endpoint allows users to calculate the signal amplitude of an event.
            """
        ),
        tags=["Signal"],
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
        use_outlier_filter = serializer.validated_data["use_outlier_filter"]

        data = PickerConfigData.from_dict(config.data)
        method = data.amplitude_config.amplitude_calculator
        calculator = amplitude_registry.get(method)
        if calculator is None:
            raise NotFound(_("Amplitude calculator not found."))

        amplitudes: list[SignalAmplitude] = []

        def calculate_amplitude(channel: ChannelConfigData) -> SignalAmplitude:
            """
            Calculate the amplitude of the event for a single channel.
            """
            ampl = calculator.calc(
                time,
                duration,
                channel.channel_id,
                organization_id,
                use_outlier_filter=use_outlier_filter,
            )
            if channel.is_analog:
                slope = channel.slope or 1
                offset = channel.offset or 0
                return SignalAmplitude(
                    time=time,
                    duration=duration,
                    amplitude=ampl.amplitude * slope + offset,
                    method=method,
                    category=AmplitudeCategory.DURATION,
                    unit=AmplitudeUnit.MM,
                    stream_id=channel.label,
                    channel_id=channel.channel_id,
                    label=channel.label,
                )
            return ampl

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(calculate_amplitude, channel)
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
