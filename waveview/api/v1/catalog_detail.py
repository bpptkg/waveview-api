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


class CatalogDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Retrieve Catalog",
        operation_description=(
            """
            Get catalog detail by catalog ID. Only users within the organization
            can view the details.
            """
        ),
        tags=["Catalog"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", CatalogSerializer),
        },
    )
    def get(
        self, request: Request, organization_id: str, volcano_id: str, catalog_id: str
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(volcano_id, "volcano_id")
        self.validate_uuid(catalog_id, "catalog_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        try:
            catalog = Catalog.objects.get(volcano_id=volcano_id, id=catalog_id)
        except Catalog.DoesNotExist:
            raise NotFound(_("Catalog not found."))

        serializer = CatalogSerializer(catalog)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Catalog",
        operation_description=(
            """
            Update the details of an existing catalog. Only organization owner
            or admin can update catalogs.
            """
        ),
        tags=["Catalog"],
        request_body=CatalogPayloadSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response("OK", CatalogSerializer),
        },
    )
    def put(
        self, request: Request, organization_id: str, volcano_id: str, catalog_id: str
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(volcano_id, "volcano_id")
        self.validate_uuid(catalog_id, "catalog_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = request.user.has_permission(
            organization, PermissionType.UPDATE_CATALOG
        )
        if not is_author and not has_permission:
            raise PermissionDenied(_("You do not have permission to update catalogs."))

        try:
            catalog = Catalog.objects.get(volcano_id=volcano_id, id=catalog_id)
        except Catalog.DoesNotExist:
            raise NotFound(_("Catalog not found."))

        serializer = CatalogPayloadSerializer(catalog, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Catalog",
        operation_description=(
            """
            Delete a catalog by catalog ID. Only organization owner or admin can
            delete catalogs.
            """
        ),
        tags=["Catalog"],
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response("No Content"),
        },
    )
    def delete(
        self, request: Request, organization_id: str, volcano_id: str, catalog_id: str
    ) -> Response:
        self.validate_uuid(organization_id, "organization_id")
        self.validate_uuid(volcano_id, "volcano_id")
        self.validate_uuid(catalog_id, "catalog_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        is_author = organization.author == request.user
        has_permission = request.user.has_permission(
            organization, PermissionType.DELETE_CATALOG
        )
        if not is_author and not has_permission:
            raise PermissionDenied(_("You do not have permission to delete catalogs."))

        try:
            catalog = Catalog.objects.get(volcano_id=volcano_id, id=catalog_id)
        except Catalog.DoesNotExist:
            raise NotFound(_("Catalog not found."))

        if catalog.is_default:
            raise PermissionDenied(_("You cannot delete the default catalog."))

        catalog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
