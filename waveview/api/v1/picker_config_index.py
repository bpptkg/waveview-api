from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.appconfig.models import PickerConfig
from waveview.appconfig.serializers import PickerConfigSerializer


class PickerConfigIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get Picker Configs",
        operation_description=(
            """
            The picker configs are a collection of data that are associated with
            an organization. This endpoint allows users to get the details of the
            picker configs. All members of the organization can view the picker
            configs.
            """
        ),
        tags=["Organization Settings"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", PickerConfigSerializer),
        },
    )
    def get(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)

        try:
            config = PickerConfig.objects.filter(
                organization=organization, volcano=volcano, is_preferred=True
            ).first()
        except PickerConfig.DoesNotExist:
            raise NotFound(_("Picker config not found."))

        serializer = PickerConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
