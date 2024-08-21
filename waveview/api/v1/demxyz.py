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
from waveview.organization.models import Organization
from waveview.volcano.header import DEMFileFormat
from waveview.volcano.models import DigitalElevationModel
from waveview.volcano.serializers import DEMXYZSerializer


class DEMXYZEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_summary=_("Get DEM XYZ"),
        operation_description=_(
            """
            Get DEM XYZ data for a volcano. The DEM data is in XYZ format. DEM
            data must be in Surfer grid format and the default one.
            """
        ),
        tags=["Volcano"],
        responses={
            status.HTTP_200_OK: openapi.Response("OK", DEMXYZSerializer),
        },
    )
    def get(
        self, request: Request, organization_id: UUID, volcano_id: UUID
    ) -> Response:
        organization = Organization.objects.get(id=organization_id)
        self.check_object_permissions(request, organization)
        volcano = self.get_volcano(organization, volcano_id)

        try:
            dem = DigitalElevationModel.objects.get(
                volcano=volcano, is_default=True, type=DEMFileFormat.SURFER_GRID
            )
        except DigitalElevationModel.DoesNotExist:
            raise NotFound(_("Default DEM not found."))

        serializer = DEMXYZSerializer(dem)
        return Response(serializer.data, status=status.HTTP_200_OK)
