from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from django.db import connection, models
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.inventory.db.schema import TimescaleSchemaEditor
from waveview.inventory.models import Channel


class StateType(models.TextChoices):
    NORMAL = "normal", "Normal"
    AT_RISK = "at_risk", "At Risk"
    NO_DATA = "no_data", "No Data"


@dataclass
class ChannelInfo:
    stream_id: str
    last_packet: datetime | None = None


@dataclass
class Status:
    state_type: StateType
    state_label: str
    state_description: str
    threshold: float
    color: str
    channels: list[ChannelInfo]


class ChannelInfoSerializer(serializers.Serializer):
    stream_id = serializers.CharField()
    last_packet = serializers.DateTimeField(allow_null=True)


class NetworkStatusSerializer(serializers.Serializer):
    state_type = serializers.ChoiceField(choices=StateType.choices)
    state_label = serializers.CharField()
    state_description = serializers.CharField()
    threshold = serializers.FloatField()
    color = serializers.CharField()
    channels = ChannelInfoSerializer(many=True)


class SeismicNetworkStatusEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get Seismic Network Status",
        operation_description=(
            """
            Get the seismic network status for an organization.
            """
        ),
        tags=["Seismic Network"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", NetworkStatusSerializer(many=True)
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Organization not found.",
            ),
        },
    )
    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        db = TimescaleSchemaEditor(connection)

        normal = Status(
            state_type=StateType.NORMAL,
            state_label="Normal",
            state_description="The channel is operating normally with no issues detected.",
            threshold=1,
            color="#28A745",
            channels=[],
        )

        at_risk = Status(
            state_type=StateType.AT_RISK,
            state_label="At Risk",
            state_description="The channel is at risk, indicating potential issues that need attention.",
            threshold=5,
            color="#DBAB09",
            channels=[],
        )

        now = timezone.now()
        one_minute_ago = now - timedelta(minutes=1)

        normal_channels: list[ChannelInfo] = []
        at_risk_channels: list[ChannelInfo] = []

        for channel in Channel.objects.filter(
            station__network__inventory__organization=organization
        ):
            stream_id = channel.stream_id
            data = db.fetch_latest_data(channel.get_datastream_id())
            if data is None:
                at_risk_channels.append(
                    ChannelInfo(stream_id=stream_id, last_packet=None)
                )
                continue

            st = data[0]
            if st >= one_minute_ago:
                normal_channels.append(ChannelInfo(stream_id=stream_id, last_packet=st))
            else:
                at_risk_channels.append(
                    ChannelInfo(stream_id=stream_id, last_packet=st)
                )

        normal_channels.sort(
            key=lambda x: x.last_packet or timezone.make_aware(datetime.min)
        )
        at_risk_channels.sort(
            key=lambda x: x.last_packet or timezone.make_aware(datetime.min)
        )

        normal.channels = normal_channels
        at_risk.channels = at_risk_channels

        serializer = NetworkStatusSerializer([normal, at_risk], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
