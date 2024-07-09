from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsOrganizationMember, IsSuperUser
from waveview.organization.models import Organization
from waveview.organization.serializers import (
    OrganizationPayloadSerializer,
    OrganizationSerializer,
)
from waveview.utils.uuid import is_valid_uuid


class OrganizationDetailEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_permissions(self) -> list:
        permissions = super().get_permissions()
        if self.request.method in ["PUT", "DELETE"]:
            permissions.append(IsSuperUser())
        return permissions

    @swagger_auto_schema(
        operation_id="Get Organization Detail",
        operation_description=(
            """
            Get organization detail by organization ID. Only members of the
            organization can view the details.
            """
        ),
        tags=["Organization"],
        responses={status.HTTP_200_OK: openapi.Response("OK", OrganizationSerializer)},
    )
    def get(self, request: Request, organization_id: str) -> Response:
        if not is_valid_uuid(organization_id):
            raise serializers.ValidationError(
                {"organization_id": _("Invalid UUID format.")},
            )

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        serializer = OrganizationSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Organization Detail",
        operation_description=(
            """
            Allows a superuser to update the details of an existing
            organization. This operation is restricted to superusers due to the
            sensitive nature of the data involved.

            The update can include changes to the organization's name, contact
            information, and other relevant details. The fields that can be
            partially updated are defined in the request payload.
            """
        ),
        tags=["Organization"],
        request_body=OrganizationPayloadSerializer,
        responses={status.HTTP_200_OK: openapi.Response("OK", OrganizationSerializer)},
    )
    def put(self, request: Request, organization_id: str) -> Response:
        if not is_valid_uuid(organization_id):
            raise serializers.ValidationError(
                {"organization_id": _("Invalid UUID format.")},
            )

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        serializer = OrganizationPayloadSerializer(
            instance=organization,
            data=request.data,
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Delete Organization",
        operation_description=(
            """
            Delete an organization. This operation is restricted to superusers
            only and requires manual intervention.

            Due to the irreversible nature of this action and its potential
            impact on related data, the deletion process is intentionally
            designed to be manual. Superusers must ensure all necessary
            precautions and data backups are taken before proceeding with
            deletion.

            This API endpoint serves as a placeholder to document the policy and
            does not directly execute organization deletions. Actual deletion
            must be performed manually by a superuser, ensuring all safety
            checks are in place.
            """
        ),
        tags=["Organization"],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", openapi.Schema(type=openapi.TYPE_OBJECT)
            )
        },
    )
    def delete(self, request: Request, organization_id: str) -> Response:
        if not is_valid_uuid(organization_id):
            raise serializers.ValidationError(
                {"organization_id": _("Invalid UUID format.")},
            )

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))
        self.check_object_permissions(request, organization)

        return Response(
            {"detail": _(f"Please delete {organization} organization manually.")},
            status=status.HTTP_200_OK,
        )
