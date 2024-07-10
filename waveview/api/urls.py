from django.urls import include, path, re_path

from .v1.account import AccountEndpoint
from .v1.auth import (
    TokenBlacklistEndpoint,
    TokenObtainPairEndpoint,
    TokenRefreshEndpoint,
    TokenVerifyEndpoint,
)
from .v1.catalog_detail import CatalogDetailEndpoint
from .v1.catalog_index import CatalogIndexEndpoint
from .v1.catchall import CatchallEndpoint
from .v1.index import IndexEndpoint
from .v1.organization_detail import OrganizationDetailEndpoint
from .v1.organization_index import OrganizationIndexEndpoint
from .v1.organization_member_detail import OrganizationMemberDetailEndpoint
from .v1.organization_member_index import OrganizationMemberIndexEndpoint
from .v1.organization_permissions import OrganizationPermissionsEndpoint
from .v1.organization_role_detail import OrganizationRoleDetailEndpoint
from .v1.organization_role_index import OrganizationRoleIndexEndpoint
from .v1.search_user import SearchUserEndpoint
from .v1.volcano_detail import VolcanoDetailEndpoint
from .v1.volcano_index import VolcanoIndexEndpoint

ORGANIZATION_URLS = [
    path(
        "",
        OrganizationIndexEndpoint.as_view(),
        name="waveview-api-1-organizatio-index",
    ),
    path(
        "permissions/",
        OrganizationPermissionsEndpoint.as_view(),
        name="waveview-api-1-organization-permissions",
    ),
    path(
        "<str:organization_id>/",
        OrganizationDetailEndpoint.as_view(),
        name="waveview-api-1-organization-detail",
    ),
    path(
        "<str:organization_id>/members/",
        OrganizationMemberIndexEndpoint.as_view(),
        name="waveview-api-1-organization-member-index",
    ),
    path(
        "<str:organization_id>/members/<str:user_id>/",
        OrganizationMemberDetailEndpoint.as_view(),
        name="waveview-api-1-organization-member-detail",
    ),
    path(
        "<str:organization_id>/roles/",
        OrganizationRoleIndexEndpoint.as_view(),
        name="waveview-api-1-organization-role-index",
    ),
    path(
        "<str:organization_id>/roles/<str:role_id>/",
        OrganizationRoleDetailEndpoint.as_view(),
        name="waveview-api-1-organization-role-detail",
    ),
]

VOLCANO_URLS = [
    path(
        "volcanoes/",
        VolcanoIndexEndpoint.as_view(),
        name="waveview-api-1-volcano-index",
    ),
    path(
        "volcanoes/<str:volcano_id>/",
        VolcanoDetailEndpoint.as_view(),
        name="waveview-api-1-volcano-detail",
    ),
]

CATALOG_URLS = [
    path(
        "catalogs/",
        CatalogIndexEndpoint.as_view(),
        name="waveview-api-1-catalog-index",
    ),
    path(
        "catalogs/<str:catalog_id>/",
        CatalogDetailEndpoint.as_view(),
        name="waveview-api-1-catalog-detail",
    ),
]

ACCOUNT_URLS = [
    path(
        "",
        AccountEndpoint.as_view(),
        name="waveview-api-1-account",
    ),
    path(
        "search/",
        SearchUserEndpoint.as_view(),
        name="waveview-api-1-account-search",
    ),
]

AUTH_URLS = [
    path(
        "token/",
        TokenObtainPairEndpoint.as_view(),
        name="waveview-api-1-auth-token",
    ),
    path(
        "token/blacklist",
        TokenBlacklistEndpoint.as_view(),
        name="waveview-api-1-auth-token",
    ),
    path(
        "token/verify/",
        TokenVerifyEndpoint.as_view(),
        name="waveview-api-1-auth-token-verify",
    ),
    path(
        "token/refresh/",
        TokenRefreshEndpoint.as_view(),
        name="waveview-api-1-auth-token-refresh",
    ),
]

urlpatterns = [
    path("organizations/", include(ORGANIZATION_URLS)),
    path("organizations/<str:organization_id>/", include(VOLCANO_URLS)),
    path(
        "organizations/<str:organization_id>/volcanoes/<str:volcano_id>/",
        include(CATALOG_URLS),
    ),
    path("account/", include(ACCOUNT_URLS)),
    path("auth/", include(AUTH_URLS)),
    re_path(r"^$", IndexEndpoint.as_view(), name="waveview-api-1-index"),
    re_path(r"^", CatchallEndpoint.as_view(), name="waveview-api-1-catchall"),
]
