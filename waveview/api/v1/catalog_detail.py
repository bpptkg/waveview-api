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
from waveview.event.serializers import CatalogPayloadSerializer, CatalogSerializer
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
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)
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
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization, PermissionType.UPDATE_CATALOG
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to update catalogs."))

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
        self,
        request: Request,
        organization_id: UUID,
        volcano_id: UUID,
        catalog_id: UUID,
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalog = self.get_catalog(volcano, catalog_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization, PermissionType.DELETE_CATALOG
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to delete catalogs."))

        if catalog.is_default:
            raise PermissionDenied(_("You cannot delete the default catalog."))

        catalog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
