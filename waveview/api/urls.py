from django.urls import include, path, re_path

from .v1.account import AccountEndpoint
from .v1.analytics.hypocenter import HypocenterEndpoint
from .v1.analytics.seismicity import SeismicityEndpoint
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
from .v1.demxyz import DEMXYZEndpoint
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

ANALYTICS_URLS = [
    path(
        "seismicity/",
        SeismicityEndpoint.as_view(),
        name="waveview-api-1-analytics-seismicity",
    ),
    path(
        "hypocenter/",
        HypocenterEndpoint.as_view(),
        name="waveview-api-1-analytics-hypocenter",
    ),
]


EVENT_ORIGIN_URLS = [
    path(
        "",
        EventOriginIndexEndpoint.as_view(),
        name="waveview-api-1-event-origin-index",
    ),
    path(
        "<uuid:origin_id>/",
        EventOriginDetailEndpoint.as_view(),
        name="waveview-api-1-event-origin-detail",
    ),
]

EVENT_URLS = [
    path(
        "",
        EventIndexEndpoint.as_view(),
        name="waveview-api-1-event-index",
    ),
    path(
        "<uuid:event_id>/",
        EventDetailEndpoint.as_view(),
        name="waveview-api-1-event-detail",
    ),
    path(
        "<uuid:event_id>/bookmark/",
        BookmarkEventEndpoint.as_view(),
        name="waveview-api-1-event-bookmark",
    ),
    path(
        "<uuid:event_id>/origin/",
        include(EVENT_ORIGIN_URLS),
    ),
]


CATALOG_URLS = [
    path(
        "",
        CatalogIndexEndpoint.as_view(),
        name="waveview-api-1-catalog-index",
    ),
    path(
        "<uuid:catalog_id>/",
        CatalogDetailEndpoint.as_view(),
        name="waveview-api-1-catalog-detail",
    ),
    path(
        "<uuid:catalog_id>/events/",
        include(EVENT_URLS),
    ),
    path(
        "<uuid:catalog_id>/analytics/",
        include(ANALYTICS_URLS),
    ),
]


EVENT_TYPE_URLS = [
    path(
        "",
        EventTypeIndexEndpoint.as_view(),
        name="waveview-api-1-event-type-index",
    ),
    path(
        "<uuid:event_type_id>/",
        EventTypeDetailEndpoint.as_view(),
        name="waveview-api-1-event-type-detail",
    ),
]

PICKER_CONFIG_URLS = [
    path(
        "",
        PickerConfigIndexEndpoint.as_view(),
        name="waveview-api-1-picker-config-index",
    ),
]

INVENTORY_URLS = [
    path(
        "",
        InventoryEndpoint.as_view(),
        name="waveview-api-1-inventory-detail",
    ),
    path(
        "networks/",
        NetworkIndexEndpoint.as_view(),
        name="waveview-api-1-inventory-network-index",
    ),
    path(
        "networks/<uuid:network_id>/",
        NetworkDetailEndpoint.as_view(),
        name="waveview-api-1-inventory-network-detail",
    ),
    path(
        "networks/<uuid:network_id>/stations/",
        StationIndexEndpoint.as_view(),
        name="waveview-api-1-inventory-station-index",
    ),
    path(
        "networks/<uuid:network_id>/stations/<uuid:station_id>/",
        StationDetailEndpoint.as_view(),
        name="waveview-api-1-inventory-station-detail",
    ),
    path(
        "networks/<uuid:network_id>/stations/<uuid:station_id>/channels/",
        ChannelIndexEndpoint.as_view(),
        name="waveview-api-1-inventory-channel-index",
    ),
    path(
        "networks/<uuid:network_id>/stations/<uuid:station_id>/channels/<uuid:channel_id>/",
        ChannelDetailEndpoint.as_view(),
        name="waveview-api-1-inventory-channel-detail",
    ),
]


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


VOLCANO_URLS = [
    path(
        "",
        VolcanoIndexEndpoint.as_view(),
        name="waveview-api-1-volcano-index",
    ),
    path(
        "<uuid:volcano_id>/",
        VolcanoDetailEndpoint.as_view(),
        name="waveview-api-1-volcano-detail",
    ),
    path(
        "<uuid:volcano_id>/demxyz/",
        DEMXYZEndpoint.as_view(),
        name="waveview-api-1-volcano-demxyz",
    ),
    path(
        "<uuid:volcano_id>/catalogs/",
        include(CATALOG_URLS),
    ),
    path(
        "<uuid:volcano_id>/picker-config/",
        include(PICKER_CONFIG_URLS),
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
        "<uuid:organization_id>/volcanoes/",
        include(VOLCANO_URLS),
    ),
    path(
        "<uuid:organization_id>/event-types/",
        include(EVENT_TYPE_URLS),
    ),
    path(
        "<uuid:organization_id>/inventory/",
        include(INVENTORY_URLS),
    ),
    path(
        "<uuid:organization_id>/services/",
        include(SERVICE_URLS),
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
        "token/blacklist/",
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
    path("event-attachments/", include(EVENT_ATTACHMENT_URLS)),
    path("account/", include(ACCOUNT_URLS)),
    path("auth/", include(AUTH_URLS)),
    re_path(r"^$", IndexEndpoint.as_view(), name="waveview-api-1-index"),
    re_path(r"^", CatchallEndpoint.as_view(), name="waveview-api-1-catchall"),
]
