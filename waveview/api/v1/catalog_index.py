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
from waveview.event.models import Catalog
from waveview.event.serializers import CatalogPayloadSerializer, CatalogSerializer
from waveview.organization.models import Organization
from waveview.organization.permissions import PermissionType


class CatalogIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Catalogs",
        operation_description=(
            """
            List all catalogs for the specified volcano and organization. Only
            members of the organization can view the catalogs.
            """
        ),
        tags=["Catalog"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", CatalogSerializer(many=True))
        },
    )
    def get(self, request: Request, organization_id: str, volcano_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(volcano_id, "volcano_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        catalogs = Catalog.objects.filter(volcano_id=volcano_id)
        serializer = CatalogSerializer(catalogs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_id="Create Catalog",
        operation_description=(
            """
            Create a new catalog for the specified volcano. Only authorized
            members of the organization that the volcano belongs to can create
            catalogs.
            """
        ),
        tags=["Catalog"],
        request_body=CatalogPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", CatalogSerializer)
        },
    )
    def post(self, request: Request, organization_id: str, volcano_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(volcano_id, "volcano_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = request.user.has_permission(
            organization_id, PermissionType.CREATE_CATALOG
        )
        if not is_author or not has_permission:
            raise PermissionDenied(_("You do not have permission to create catalogs."))

        serializer = CatalogPayloadSerializer(
            data=request.data,
            context={"request": request, "volcano_id": volcano_id},
        )
        serializer.is_valid(raise_exception=True)
        catalog = serializer.save()
        return Response(CatalogSerializer(catalog).data, status=status.HTTP_201_CREATED)
