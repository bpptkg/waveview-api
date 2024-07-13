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
from waveview.inventory.serializers import InventorySerializer
from waveview.organization.models import Organization


class InventoryEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get Inventory",
        operation_description=(
            """
            The inventory is a collection of networks, stations, and channels
            that are associated with an organization. This endpoint allows users
            to  get the details of the organization inventory. All members of
            the organization can view the inventory.
            """
        ),
        tags=["Inventory"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", InventorySerializer),
        },
    )
    def get(self, request: Request, organization_id: str) -> Response:
        self.validate_uuid(organization_id, "organization_id")

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        inventory = organization.inventory
        serializer = InventorySerializer(inventory)
        return Response(serializer.data, status=status.HTTP_200_OK)
