from django.urls import path, re_path

from .v1.account import AccountEndpoint
from .v1.auth import (
    TokenBlacklistEndpoint,
    TokenObtainPairEndpoint,
    TokenRefreshEndpoint,
    TokenVerifyEndpoint,
)
from .v1.catchall import CatchallEndpoint
from .v1.index import IndexEndpoint
from .v1.organization_detail import OrganizationDetailEndpoint
from .v1.organization_index import OrganizationIndexEndpoint
from .v1.organization_member_detail import OrganizationMemberDetailEndpoint
from .v1.organization_member_index import OrganizationMemberIndexEndpoint
from .v1.search_user import SearchUserEndpoint

urlpatterns = [
    path(
        "organizations/",
        OrganizationIndexEndpoint.as_view(),
        name="waveview-api-1-organizatio-index",
    ),
    path(
        "organizations/<str:organization_id>/",
        OrganizationDetailEndpoint.as_view(),
        name="waveview-api-1-organization-detail",
    ),
    path(
        "organizations/<str:organization_id>/members/",
        OrganizationMemberIndexEndpoint.as_view(),
        name="waveview-api-1-organization-member-index",
    ),
    path(
        "organizations/<str:organization_id>/members/<str:user_id>/",
        OrganizationMemberDetailEndpoint.as_view(),
        name="waveview-api-1-organization-member-detail",
    ),
    path("account/", AccountEndpoint.as_view(), name="waveview-api-1-account"),
    path(
        "users/search/",
        SearchUserEndpoint.as_view(),
        name="waveview-api-1-users-search",
    ),
    path(
        "login/",
        TokenObtainPairEndpoint.as_view(),
        name="waveview-api-1-login",
    ),
    path(
        "logout/",
        TokenBlacklistEndpoint.as_view(),
        name="waveview-api-1-logout",
    ),
    path(
        "token/verify/",
        TokenVerifyEndpoint.as_view(),
        name="waveview-api-1-token-verify",
    ),
    path(
        "token/refresh/",
        TokenRefreshEndpoint.as_view(),
        name="waveview-api-1-token-refresh",
    ),
    re_path("^$", IndexEndpoint.as_view(), name="waveview-api-1-index"),
    re_path("^", CatchallEndpoint.as_view(), name="waveview-api-1-catchall"),
]
