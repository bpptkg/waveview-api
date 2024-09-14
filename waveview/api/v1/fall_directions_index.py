from uuid import UUID

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.observation.models import FallDirection
from waveview.observation.serializers import FallDirectionSerializer


class FallDirectionIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="List Fall Directions",
        operation_description=(
            """
            List all fall directions within the organization. Only users within the
            organization can view the fall directions.
            """
        ),
        tags=["Observation"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", FallDirectionSerializer(many=True)
            ),
        },
    )
    def get(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = self.get_organization(organization_id)
        volcano = self.get_volcano(organization, volcano_id)
        self.check_object_permissions(request, organization)
        fall_directions = FallDirection.objects.filter(volcano=volcano)
        serializer = FallDirectionSerializer(fall_directions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
