from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.organization.permissions import PermissionType
from waveview.volcano.models import Volcano
from waveview.volcano.serializers import VolcanoPayloadSerializer, VolcanoSerializer


class VolcanoIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Volcanoes",
        operation_description=(
            """
            Get list of all managed volcanoes within organization. Only users
            within the organization can list volcanoes.
            """
        ),
        tags=["Volcano"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", VolcanoSerializer(many=True)),
        },
    )
    def get(self, request: Request, organization_id: UUID) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        volcanoes = Volcano.objects.filter(organization_id=organization_id)
        serializer = VolcanoSerializer(volcanoes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Volcano",
        operation_description=(
            """
            Create a new volcano. Only organization owner or admin can create
            volcanoes.
            """
        ),
        tags=["Volcano"],
        request_body=VolcanoPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", VolcanoSerializer),
        },
    )
    def post(self, request: Request, organization_id: UUID) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.CREATE_VOLCANO
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to create volcanoes."),
            )

        serializer = VolcanoPayloadSerializer(
            data=request.data,
            context={"request": request, "organization_id": organization_id},
        )
        serializer.is_valid(raise_exception=True)
        volcano = serializer.save()
        return Response(VolcanoSerializer(volcano).data, status=status.HTTP_201_CREATED)
