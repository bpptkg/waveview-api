import base64
import io
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

import numpy as np
from django.db import connection
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from obspy import Inventory as ObspyInventory
from obspy import Stream, read_inventory
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.inventory.datastream import DataStream
from waveview.inventory.header import FieldType
from waveview.inventory.models import Channel, Inventory


@dataclass
class ResultInfo:
    image: str
    empty: bool
    amplitude_max: float | None
    amplitude_min: float | None
    amplitude_peak: float | None
    amplitude_unit: str


class RemoveResponsePlotter:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory
        self.datastream = DataStream(connection)

    def plot(
        self, channel: Channel, starttime: datetime, endtime: datetime, **options: dict
    ) -> ResultInfo:
        st = self.datastream.get_waveform(channel.id, starttime, endtime)
        st.detrend("demean")
        st.merge(fill_value=0)
        buf = io.BytesIO()
        output = options.get("output", FieldType.DEF)

        def remove_response(st: Stream) -> Stream:
            for inv_file in self.inventory.files.all():
                inv: ObspyInventory = read_inventory(inv_file.file)
                try:
                    st.remove_response(inventory=inv, plot=buf, **options)
                    return st
                except Exception:
                    pass
            raise Exception("No matching inventory found.")

        st = remove_response(st)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()

        if len(st) == 0:
            amplitude_max = None
            amplitude_min = None
            amplitude_peak = None
        else:
            data = st[0].data
            amplitude_max = np.nanmax(data)
            amplitude_min = np.nanmin(data)
            amplitude_peak = (amplitude_max - amplitude_min) / 2
            if np.isnan(amplitude_max):
                amplitude_max = None

        if output == FieldType.DISP:
            amplitude_unit = "m"
        elif output == FieldType.VEL:
            amplitude_unit = "m/s"
        elif output == FieldType.ACC:
            amplitude_unit = "m/s^2"
        else:
            amplitude_unit = "units"

        response = ResultInfo(
            image=f"data:image/png;base64,{img_base64}",
            empty=img_base64 == "",
            amplitude_max=amplitude_max,
            amplitude_min=amplitude_min,
            amplitude_peak=amplitude_peak,
            amplitude_unit=amplitude_unit,
        )
        return response


class PlotRemoveResponsePayloadSerializer(serializers.Serializer):
    channel_id = serializers.UUIDField(help_text=_("The channel ID of the signal."))
    time = serializers.DateTimeField(
        help_text=_("The time of the query in ISO 8601 format.")
    )
    duration = serializers.FloatField(
        help_text=_("The duration of the query in seconds.")
    )
    output = serializers.ChoiceField(
        choices=FieldType.choices, help_text=_("The output type of the signal.")
    )
    water_level = serializers.FloatField(
        help_text=_("The water level of the signal."), default=None, allow_null=True
    )
    pre_filt = serializers.ListField(
        child=serializers.FloatField(),
        help_text=_("The pre-filter values for the signal."),
        default=None,
        allow_null=True,
    )
    zero_mean = serializers.BooleanField(
        help_text=_("Whether to zero mean the signal."), default=True
    )
    taper = serializers.BooleanField(
        help_text=_("Whether to taper the signal."), default=True
    )
    taper_fraction = serializers.FloatField(
        help_text=_("The taper fraction of the signal."), default=0.05
    )

    def validate_channel_id(self, value: str) -> str:
        try:
            Channel.objects.get(id=value)
        except Channel.DoesNotExist:
            raise serializers.ValidationError(_("Channel does not exist."))
        return value

    def validate_pre_filt(self, value: list | None) -> list | None:
        if value is None:
            return None
        if len(value) != 4:
            raise serializers.ValidationError(_("Pre-filter values must be length 4."))
        return value


class PlotRemoveResponseSerializer(serializers.Serializer):
    image = serializers.CharField(
        help_text=_("The image of the signal encoded in base64.")
    )
    empty = serializers.BooleanField(
        help_text=_("Whether the signal is empty."), default=False
    )
    error = serializers.CharField(
        help_text=_("The error message if any."), default=None
    )
    amplitude_max = serializers.FloatField(
        help_text=_("The maximum amplitude of the signal."), default=0
    )
    amplitude_min = serializers.FloatField(
        help_text=_("The minimum amplitude of the signal."), default=0
    )
    amplitude_peak = serializers.FloatField(
        help_text=_("The peak amplitude of the signal."), default=0
    )
    amplitude_unit = serializers.CharField(
        help_text=_("The unit of the amplitude of the signal."), default=""
    )


class PlotRemoveResponseEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Plot Remove Response",
        operation_description=(
            """
            This endpoint allows users to plot the remove instrument response of a signal.
            """
        ),
        tags=["Signal"],
        request_body=PlotRemoveResponsePayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", PlotRemoveResponseSerializer),
        },
    )
    def post(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        self.get_volcano(organization, volcano_id)

        serializer = PlotRemoveResponsePayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        channel_id = serializer.validated_data["channel_id"]
        time = serializer.validated_data["time"]
        duration = serializer.validated_data["duration"]
        output = serializer.validated_data["output"]
        water_level = serializer.validated_data["water_level"]
        pre_filt = serializer.validated_data["pre_filt"]
        zero_mean = serializer.validated_data["zero_mean"]
        taper = serializer.validated_data["taper"]
        taper_fraction = serializer.validated_data["taper_fraction"]

        inventory = organization.inventory
        channel = Channel.objects.get(id=channel_id)
        try:
            starttime = time
            endtime = time + timedelta(seconds=duration)
            plotter = RemoveResponsePlotter(inventory)
            result = plotter.plot(
                channel,
                starttime,
                endtime,
                output=output,
                water_level=water_level,
                pre_filt=pre_filt,
                zero_mean=zero_mean,
                taper=taper,
                taper_fraction=taper_fraction,
            )
            return Response(
                PlotRemoveResponseSerializer(result).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            raise serializers.ValidationError(str(e))
