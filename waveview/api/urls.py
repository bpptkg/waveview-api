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
from .v1.channel_detail import ChannelDetailEndpoint
from .v1.channel_index import ChannelIndexEndpoint
from .v1.event_attachment_detail import EventAttachmentDetailEndpoint
from .v1.event_attachment_index import EventAttachmentUploadEndpoint
from .v1.event_bookmark import BookmarkEventEndpoint
from .v1.event_detail import EventDetailEndpoint
from .v1.event_index import EventIndexEndpoint
from .v1.event_origin_detail import EventOriginDetailEndpoint
from .v1.event_origin_index import EventOriginIndexEndpoint
from .v1.event_type_detail import EventTypeDetailEndpoint
from .v1.event_type_index import EventTypeIndexEndpoint
from .v1.index import IndexEndpoint
from .v1.inventory import InventoryEndpoint
from .v1.network_detail import NetworkDetailEndpoint
from .v1.network_index import NetworkIndexEndpoint
from .v1.organization_detail import OrganizationDetailEndpoint
from .v1.organization_index import OrganizationIndexEndpoint
from .v1.organization_member_detail import OrganizationMemberDetailEndpoint
from .v1.organization_member_index import OrganizationMemberIndexEndpoint
from .v1.organization_permissions import OrganizationPermissionsEndpoint
from .v1.organization_role_detail import OrganizationRoleDetailEndpoint
from .v1.organization_role_index import OrganizationRoleIndexEndpoint
from .v1.organization_settings_index import OrganizationSettingsIndexEndpoint
from .v1.picker_config_index import PickerConfigIndexEndpoint
from .v1.registration import AccountRegistrationEndpoint
from .v1.search_user import SearchUserEndpoint
from .v1.seedlink import (
    SeedLinkContainerRestartEndpoint,
    SeedLinkContainerStartEndpoint,
    SeedLinkContainerStopEndpoint,
)
from .v1.station_detail import StationDetailEndpoint
from .v1.station_index import StationIndexEndpoint
from .v1.volcano_detail import VolcanoDetailEndpoint
from .v1.volcano_index import VolcanoIndexEndpoint

SERVICE_URLS = [
    path(
        "seedlink/start/",
        SeedLinkContainerStartEndpoint.as_view(),
        name="waveview-api-1-seedlink-start",
    ),
    path(
        "seedlink/stop/",
        SeedLinkContainerStopEndpoint.as_view(),
        name="waveview-api-1-seedlink-stop",
    ),
    path(
        "seedlink/restart/",
        SeedLinkContainerRestartEndpoint.as_view(),
        name="waveview-api-1-seedlink-restart",
    ),
]

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
        "<uuid:organization_id>/",
        OrganizationDetailEndpoint.as_view(),
        name="waveview-api-1-organization-detail",
    ),
    path(
        "<uuid:organization_id>/members/",
        OrganizationMemberIndexEndpoint.as_view(),
        name="waveview-api-1-organization-member-index",
    ),
    path(
        "<uuid:organization_id>/members/<uuid:user_id>/",
        OrganizationMemberDetailEndpoint.as_view(),
        name="waveview-api-1-organization-member-detail",
    ),
    path(
        "<uuid:organization_id>/roles/",
        OrganizationRoleIndexEndpoint.as_view(),
        name="waveview-api-1-organization-role-index",
    ),
    path(
        "<uuid:organization_id>/roles/<uuid:role_id>/",
        OrganizationRoleDetailEndpoint.as_view(),
        name="waveview-api-1-organization-role-detail",
    ),
    path(
        "<uuid:organization_id>/settings/",
        OrganizationSettingsIndexEndpoint.as_view(),
        name="waveview-api-1-organization-settings",
    ),
]

VOLCANO_URLS = [
    path(
        "volcanoes/",
        VolcanoIndexEndpoint.as_view(),
        name="waveview-api-1-volcano-index",
    ),
    path(
        "volcanoes/<uuid:volcano_id>/",
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
        "catalogs/<uuid:catalog_id>/",
        CatalogDetailEndpoint.as_view(),
        name="waveview-api-1-catalog-detail",
    ),
]

EVENT_URLS = [
    path(
        "events/",
        EventIndexEndpoint.as_view(),
        name="waveview-api-1-event-index",
    ),
    path(
        "events/<uuid:event_id>/",
        EventDetailEndpoint.as_view(),
        name="waveview-api-1-event-detail",
    ),
    path(
        "events/<uuid:event_id>/bookmark/",
        BookmarkEventEndpoint.as_view(),
        name="waveview-api-1-event-bookmark",
    ),
]

EVENT_ATTACHMENT_URLS = [
    path(
        "",
        EventAttachmentUploadEndpoint.as_view(),
        name="waveview-api-1-event-attachment",
    ),
    path(
        "<uuid:attachment_id>/",
        EventAttachmentDetailEndpoint.as_view(),
        name="waveview-api-1-event-attachment-detail",
    ),
]

EVENT_ORIGIN_URLS = [
    path(
        "origins/",
        EventOriginIndexEndpoint.as_view(),
        name="waveview-api-1-event-origin-index",
    ),
    path(
        "origins/<uuid:origin_id>/",
        EventOriginDetailEndpoint.as_view(),
        name="waveview-api-1-event-origin-detail",
    ),
]

EVENT_TYPE_URLS = [
    path(
        "event-types/",
        EventTypeIndexEndpoint.as_view(),
        name="waveview-api-1-event-type-index",
    ),
    path(
        "event-types/<uuid:event_type_id>/",
        EventTypeDetailEndpoint.as_view(),
        name="waveview-api-1-event-type-detail",
    ),
]

INVENTORY_URLS = [
    path(
        "inventory/",
        InventoryEndpoint.as_view(),
        name="waveview-api-1-inventory-detail",
    ),
    path(
        "inventory/networks/",
        NetworkIndexEndpoint.as_view(),
        name="waveview-api-1-inventory-network-index",
    ),
    path(
        "inventory/networks/<uuid:network_id>/",
        NetworkDetailEndpoint.as_view(),
        name="waveview-api-1-inventory-network-detail",
    ),
    path(
        "inventory/networks/<uuid:network_id>/stations/",
        StationIndexEndpoint.as_view(),
        name="waveview-api-1-inventory-station-index",
    ),
    path(
        "inventory/networks/<uuid:network_id>/stations/<uuid:station_id>/",
        StationDetailEndpoint.as_view(),
        name="waveview-api-1-inventory-station-detail",
    ),
    path(
        "inventory/networks/<uuid:network_id>/stations/<uuid:station_id>/channels/",
        ChannelIndexEndpoint.as_view(),
        name="waveview-api-1-inventory-channel-index",
    ),
    path(
        "inventory/networks/<uuid:network_id>/stations/<uuid:station_id>/channels/<uuid:channel_id>/",
        ChannelDetailEndpoint.as_view(),
        name="waveview-api-1-inventory-channel-detail",
    ),
]

PICKER_URLS = [
    path(
        "picker-config/",
        PickerConfigIndexEndpoint.as_view(),
        name="waveview-api-1-picker-config-index",
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
    path(
        "register/",
        AccountRegistrationEndpoint.as_view(),
        name="waveview-api-1-account-register",
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
    path("organizations/<uuid:organization_id>/", include(VOLCANO_URLS)),
    path("organizations/<uuid:organization_id>/", include(EVENT_TYPE_URLS)),
    path("organizations/<uuid:organization_id>/", include(INVENTORY_URLS)),
    path("organizations/<uuid:organization_id>/", include(PICKER_URLS)),
    path("organizations/<uuid:organization_id>/services/", include(SERVICE_URLS)),
    path(
        "organizations/<uuid:organization_id>/volcanoes/<uuid:volcano_id>/",
        include(CATALOG_URLS),
    ),
    path(
        "organizations/<uuid:organization_id>/catalogs/<uuid:catalog_id>/",
        include(EVENT_URLS),
    ),
    path(
        "organizations/<uuid:organization_id>/catalogs/<uuid:catalog_id>/events/<uuid:event_id>/",
        include(EVENT_ORIGIN_URLS),
    ),
    path("event-attachments/", include(EVENT_ATTACHMENT_URLS)),
    path("account/", include(ACCOUNT_URLS)),
    path("auth/", include(AUTH_URLS)),
    re_path(r"^$", IndexEndpoint.as_view(), name="waveview-api-1-index"),
    re_path(r"^", CatchallEndpoint.as_view(), name="waveview-api-1-catchall"),
]
