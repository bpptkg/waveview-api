from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember
from waveview.organization.permissions import PermissionType


class PermissionChoiceSerializer(serializers.Serializer):
    value = serializers.CharField(help_text=_("Permission value."))
    label = serializers.CharField(help_text=_("Permission label."))


class OrganizationPermissionsEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    @swagger_auto_schema(
        operation_id="Get Organization Permissions",
        operation_description=(
            """
            Get a list of permissions available for an organization. Permissions
            are used to define the actions that can be performed by users within
            the organization.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", PermissionChoiceSerializer(many=True)
            )
        },
    )
    def get(self, request: Request) -> Response:
        permissions = []
        for item in PermissionType.choices:
            permissions.append({"value": item[0], "label": item[1]})

        return Response(permissions, status=status.HTTP_200_OK)
