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
from waveview.appconfig.serializers import (
    PickerConfigPayloadSerializer,
    PickerConfigSerializer,
)


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
        tags=["App Config"],
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
        user = request.user

        try:
            orgconfig = PickerConfig.objects.filter(
                organization=organization, volcano=volcano
            ).get()
        except PickerConfig.DoesNotExist:
            raise NotFound(_("Picker config not found."))

        try:
            config = PickerConfig.objects.filter(user=user, volcano=volcano).get()
        except PickerConfig.DoesNotExist:
            config = None

        if config:
            config.merge(orgconfig)
        else:
            config = orgconfig
        serializer = PickerConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Picker Configs",
        operation_description=(
            """
            Update picker configs for certain users.
            """
        ),
        tags=["App Config"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", PickerConfigSerializer),
        },
    )
    def put(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        user = request.user

        serializer = PickerConfigPayloadSerializer(
            data=request.data,
            context={"user": user, "volcano": volcano, "organization": organization},
        )
        serializer.is_valid(raise_exception=True)
        config = serializer.save()

        serializer = PickerConfigSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
