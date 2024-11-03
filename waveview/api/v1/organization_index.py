from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsSuperUser
from waveview.organization.models import Organization
from waveview.organization.serializers import (
    OrganizationPayloadSerializer,
    OrganizationSerializer,
)


class OrganizationIndexEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    def get_permissions(self) -> list:
        permissions = super().get_permissions()
        if self.request.method == "POST":
            permissions.append(IsSuperUser())
        return permissions

    @swagger_auto_schema(
        operation_id="List Organizations",
        operation_description=(
            """
            Get list of organizations which the user is a member of.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", OrganizationSerializer(many=True)
            ),
        },
    )
    def get(self, request: Request) -> Response:
        organizations = Organization.objects.filter(
            Q(members=request.user) | Q(author=request.user)
        ).all()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Create Organization",
        operation_description=(
            """
            Create a new organization. Only the superuser can create an
            organization.
            """
        ),
        tags=["Organization"],
        request_body=OrganizationPayloadSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                "Created", OrganizationSerializer
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = OrganizationPayloadSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            OrganizationSerializer(instance).data, status=status.HTTP_201_CREATED
        )
