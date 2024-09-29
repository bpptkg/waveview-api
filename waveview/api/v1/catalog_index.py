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
from waveview.event.models import Catalog
from waveview.event.serializers import CatalogPayloadSerializer, CatalogSerializer
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
            status.HTTP_200_OK: openapi.Response(
                "OK",
                CatalogSerializer(many=True),
            )
        },
    )
    def get(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)
        catalogs = Catalog.objects.filter(volcano=volcano)
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
            status.HTTP_201_CREATED: openapi.Response("Created", CatalogSerializer),
        },
    )
    def post(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)

        is_author = organization.author == request.user
        has_permission = is_author or request.user.has_permission(
            organization_id, PermissionType.CREATE_CATALOG
        )
        if not has_permission:
            raise PermissionDenied(_("You do not have permission to create catalogs."))

        serializer = CatalogPayloadSerializer(
            data=request.data,
            context={"request": request, "volcano_id": volcano.id},
        )
        serializer.is_valid(raise_exception=True)
        catalog = serializer.save()
        return Response(CatalogSerializer(catalog).data, status=status.HTTP_201_CREATED)
