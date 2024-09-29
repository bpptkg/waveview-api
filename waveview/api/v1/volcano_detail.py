from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.organization.permissions import PermissionType
from waveview.volcano.models import Volcano
from waveview.volcano.serializers import VolcanoPayloadSerializer, VolcanoSerializer


class VolcanoDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Volcano",
        operation_description=(
            """
            Get volcano detail by volcano ID. Only users within the organization
            can view the details.
            """
        ),
        tags=["Volcano"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", VolcanoSerializer),
        },
    )
    def get(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        try:
            volcano = Volcano.objects.filter(organization_id=organization_id).get(
                id=volcano_id
            )
        except Volcano.DoesNotExist:
            raise NotFound(_("Volcano not found."))

        serializer = VolcanoSerializer(volcano)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Volcano",
        operation_description=(
            """
            Update the details of an existing volcano. Only organization owner
            or admin can update volcanoes.
            """
        ),
        tags=["Volcano"],
        request_body=VolcanoPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", VolcanoSerializer),
        },
    )
    def put(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.UPDATE_VOLCANO
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to update volcanoes."),
            )

        try:
            volcano = Volcano.objects.filter(organization_id=organization_id).get(
                id=volcano_id
            )
        except Volcano.DoesNotExist:
            raise NotFound(_("Volcano not found."))

        serializer = VolcanoPayloadSerializer(volcano, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        volcano = serializer.save()
        return Response(VolcanoSerializer(volcano).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Volcano",
        operation_description=(
            """
            Delete an existing volcano. This operation is restricted to
            superusers only and requires manual intervention.

            Due to the irreversible nature of this action and its potential
            impact on related data, the deletion process is intentionally
            designed to be manual. Superusers must ensure all necessary
            precautions and data backups are taken before proceeding with
            deletion.

            This API endpoint serves as a placeholder to document the policy and
            does not directly execute organization deletions. Actual deletion
            must be performed manually by a superuser, ensuring all safety
            checks are in place.
            """
        ),
        tags=["Volcano"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
        },
    )
    def delete(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.DELETE_VOLCANO
        )
        if not has_permission:
            raise PermissionDenied(
                _("You do not have permission to delete volcanoes."),
            )

        try:
            volcano = Volcano.objects.filter(organization_id=organization_id).get(
                id=volcano_id
            )
        except Volcano.DoesNotExist:
            raise NotFound(_("Volcano not found."))

        return Response(
            {"detail": _(f"Please delete {volcano} volcano manually.")},
            status=status.HTTP_200_OK,
        )
