import typing

from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request


class FlexiblePageNumberPagination(PageNumberPagination):
    page_size = 20
    page_query_param = "page"
    page_query_description = _(
        """
        A page number within the paginated result set. Pagination only active if
        `page` exists in the query parameter.
        """
    )
    page_size_query_param = "page_size"
    page_size_query_description = _(
        """
        Number of results to return per page. Default to 20 items.
        """
    )
    max_page_size = 500

    def get_page_size(self, request: Request) -> typing.Optional[int]:
        if request.query_params.get(self.page_query_param):
            return super().get_page_size(request)
        return None


class StrictPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_query_param = "page"
    page_query_description = _(
        """
        A page number within the paginated result set. Pagination is always
        active.
        """
    )
    page_size_query_param = "page_size"
    page_size_query_description = _(
        """
        Number of results to return per page. Default to 20 items.
        """
    )
    max_page_size = 500
