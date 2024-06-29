import logging

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

logger = logging.getLogger(__name__)


class TokenObtainPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField(
        help_text=_(
            """
            Bearer access token that can be used to authenticate the request by
            adding the token in the Authorization header.
            """
        )
    )
    refresh = serializers.CharField(
        help_text=_(
            """
            Refresh token to be used to obtain new access token once the access
            token has been expired without needing the user to login again.
            """
        )
    )

    def create(self, validated_data: dict) -> dict:
        raise NotImplementedError()

    def update(self, instance: object, validated_data: dict) -> object:
        raise NotImplementedError()


class TokenObtainPairEndpoint(TokenObtainPairView):
    @swagger_auto_schema(
        operation_id="Login",
        operation_description=(
            """
            Login by taking a set of user credentials and returns an access and
            refresh JSON web token pair to prove the authentication of those
            credentials.
            """
        ),
        security=[],
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", TokenObtainPairResponseSerializer
            ),
        },
        tags=["Account"],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField(
        help_text=_("New access token to authenticate the request.")
    )

    def create(self, validated_data: dict) -> dict:
        raise NotImplementedError()

    def update(self, instance: dict, validated_data: dict) -> dict:
        raise NotImplementedError()


class TokenRefreshEndpoint(TokenRefreshView):
    @swagger_auto_schema(
        operation_id="Refresh Token",
        operation_description=(
            """
            Takes a refresh type JSON web token and returns an access type JSON
            web token if the refresh token is valid.
            """
        ),
        responses={
            status.HTTP_200_OK: openapi.Response("OK", TokenRefreshResponseSerializer),
        },
        tags=["Account"],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class TokenVerifyResponseSerializer(serializers.Serializer):
    def create(self, validated_data: dict) -> dict:
        raise NotImplementedError()

    def update(self, instance: object, validated_data: dict) -> object:
        raise NotImplementedError()


class TokenVerifyEndpoint(TokenVerifyView):
    @swagger_auto_schema(
        operation_id="Verify Token",
        operation_description=(
            """
            Takes a sliding JSON web token and verify HMAC-signed token without
            having access to the signing key.
            """
        ),
        responses={
            status.HTTP_200_OK: openapi.Response("OK", TokenVerifyResponseSerializer),
        },
        tags=["Account"],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class TokenBlacklistResponseSerializer(serializers.Serializer):
    def create(self, validated_data: dict) -> dict:
        raise NotImplementedError()

    def update(self, instance: object, validated_data: dict) -> object:
        raise NotImplementedError()


class TokenBlacklistEndpoint(TokenBlacklistView):
    @swagger_auto_schema(
        operation_id="Logout",
        operation_description=(
            """
            Logout by taking a refresh type JSON web token and add them to
            blacklisted token lists. Any subsequent usage of this access token
            will become invalid.
            """
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                "OK", TokenBlacklistResponseSerializer
            ),
        },
        tags=["Account"],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)
