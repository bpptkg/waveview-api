from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.users.serializers import UserDetailSerializer, UserUpdatePayloadSerializer


class AccountEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="Get Account",
        operation_description=(
            """
            Get user account information.
            """
        ),
        tags=["Account"],
        responses={status.HTTP_200_OK: openapi.Response("OK", UserDetailSerializer)},
    )
    def get(self, request: Request) -> Response:
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_id="Update Account",
        operation_description=(
            """
            Update user account information.
            """
        ),
        tags=["Account"],
        request_body=UserUpdatePayloadSerializer,
        responses={status.HTTP_200_OK: openapi.Response("OK", UserDetailSerializer)},
    )
    def put(self, request: Request) -> Response:
        serializer = UserUpdatePayloadSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            UserDetailSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )
