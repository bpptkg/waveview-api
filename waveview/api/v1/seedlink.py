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
from waveview.inventory.models import Inventory
from waveview.inventory.seedlink.container import ContainerManager
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class SeedLinkContainerStartEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Start SeedLink Container",
        operation_description=(
            """
            Start the SeedLink container. This will start the SeedLink service
            in the organization inventory and begin streaming data.
            """
        ),
        tags=["Services"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK"),
        },
    )
    def post(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to manage inventory."))

        inventory: Inventory = organization.inventory
        container_manager = ContainerManager(inventory)
        container_manager.start()
        return Response(status=status.HTTP_200_OK)


class SeedLinkContainerStopEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Stop SeedLink Container",
        operation_description=(
            """
            Stop the SeedLink container. This will stop the SeedLink service in
            the organization inventory and stop streaming data.
            """
        ),
        tags=["Services"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK"),
        },
    )
    def post(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to manage inventory."))

        inventory: Inventory = organization.inventory
        container_manager = ContainerManager(inventory)
        container_manager.stop()
        return Response(status=status.HTTP_200_OK)


class SeedLinkContainerRestartEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Restart SeedLink Container",
        operation_description=(
            """
            Restart the SeedLink container. This will restart the SeedLink
            service in the organization inventory and restart streaming data.
            """
        ),
        tags=["Services"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK"),
        },
    )
    def post(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.MANAGE_INVENTORY
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to manage inventory."))

        inventory: Inventory = organization.inventory
        container_manager = ContainerManager(inventory)
        container_manager.restart()
        return Response(status=status.HTTP_200_OK)
