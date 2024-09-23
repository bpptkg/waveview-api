from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.appconfig.models import PickerConfig
from waveview.appconfig.serializers import PickerConfigSerializer


class PickerConfigResetEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Reset Picker Configs",
        operation_description=(
            """
            Reset picker configs for certain users.
            """
        ),
        tags=["App Config"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", PickerConfigSerializer),
        },
    )
    def post(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        user = request.user

        try:
            org_config = PickerConfig.objects.filter(
                organization=organization, volcano=volcano
            ).get()
        except PickerConfig.DoesNotExist:
            org_config = None

        if org_config:
            data = org_config.data
        else:
            data = {}
        config, __ = PickerConfig.objects.update_or_create(
            user=user, volcano=volcano, defaults={"data": data}
        )

        serializer = PickerConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
