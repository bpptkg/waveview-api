from django.urls import path

from .endpoints.auth import (
    TokenBlacklistEndpoint,
    TokenObtainPairEndpoint,
    TokenRefreshEndpoint,
    TokenVerifyEndpoint,
)

urlpatterns = [
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
]
