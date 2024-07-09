import typing

from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.pagination import BasePagination
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from waveview.api.permissions import NoPermission
from waveview.utils.uuid import is_valid_uuid

DEFAULT_AUTHENTICATION = [JWTAuthentication, SessionAuthentication]


class Endpoint(APIView):
    """Base API endpoint."""

    authentication_classes: typing.List[typing.Type[BaseAuthentication]] = (
        DEFAULT_AUTHENTICATION
    )
    permission_classes: typing.List[typing.Type[BasePermission]] = [NoPermission]

    pagination_class: typing.Optional[typing.Type[BasePagination]] = None

    @property
    def paginator(self) -> typing.Optional[BasePagination]:
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset: QuerySet) -> typing.Optional[QuerySet]:
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data: typing.Any) -> Response:
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
