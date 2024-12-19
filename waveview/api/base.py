from typing import Any, List, Optional, Type

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.pagination import BasePagination
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from waveview.api.permissions import NoPermission
from waveview.event.models import Catalog, Event
from waveview.organization.models import Organization
from waveview.utils.uuid import is_valid_uuid
from waveview.volcano.models import Volcano

DEFAULT_AUTHENTICATION = [JWTAuthentication, SessionAuthentication]


class Endpoint(APIView):
    """Base API endpoint."""

    authentication_classes: List[Type[BaseAuthentication]] = DEFAULT_AUTHENTICATION
    permission_classes: List[Type[BasePermission]] = [NoPermission]
    pagination_class: Optional[Type[BasePagination]] = None

    @property
    def paginator(self) -> Optional[BasePagination]:
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset: QuerySet) -> Optional[QuerySet]:
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data: Any) -> Response:
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def validate_uuid(self, value: str, field: str) -> str:
        """Validate UUID format."""
        if not is_valid_uuid(value):
            raise serializers.ValidationError({field: _("Invalid UUID format.")})
        return value

    def get_organization(self, organization_id: str) -> Organization:
        try:
            return Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            raise NotFound(_("Organization not found."))

    def get_volcano(self, organization: Organization, volcano_id: str) -> Volcano:
        try:
            return Volcano.objects.get(organization=organization, id=volcano_id)
        except Volcano.DoesNotExist:
            raise NotFound(_("Volcano not found."))

    def get_catalog(self, volcano: Volcano, catalog_id: str) -> Catalog:
        try:
            return Catalog.objects.get(volcano=volcano, id=catalog_id)
        except Catalog.DoesNotExist:
            raise NotFound(_("Catalog not found."))

    def get_event(self, catalog: Catalog, event_id: str) -> Event:
        try:
            return Event.objects.get(catalog=catalog, id=event_id)
        except Event.DoesNotExist:
            raise NotFound(_("Event not found."))
