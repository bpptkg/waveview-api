from typing import Optional

from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.utils.urls import remove_query_param, replace_query_param


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

    def get_page_size(self, request: Request) -> Optional[int]:
        if request.query_params.get(self.page_query_param):
            return super().get_page_size(request)
        return None

    def get_next_link(self) -> Optional[str]:
        if not self.page.has_next():
            return None
        url = self.request.get_full_path()
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self) -> Optional[str]:
        if not self.page.has_previous():
            return None
        url = self.request.get_full_path()
        page_number = self.page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)


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

    def get_next_link(self) -> Optional[str]:
        if not self.page.has_next():
            return None
        url = self.request.get_full_path()
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self) -> Optional[str]:
        if not self.page.has_previous():
            return None
        url = self.request.get_full_path()
        page_number = self.page.previous_page_number()
        if page_number == 1:
            return remove_query_param(url, self.page_query_param)
        return replace_query_param(url, self.page_query_param, page_number)
