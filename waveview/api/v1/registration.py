from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.api.permissions import IsSuperUser
from waveview.users.serializers import RegisterUserSerializer, UserSerializer


class AccountRegistrationEndpoint(Endpoint):
    permission_classes = [IsAuthenticated, IsSuperUser]

    @swagger_auto_schema(
        operation_id="Register an Account",
        operation_description=(
            """
            Register a new user account. Only superusers can register new users.
            """
        ),
        tags=["Account"],
        request_body=RegisterUserSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response("Created", UserSerializer),
            status.HTTP_400_BAD_REQUEST: openapi.Response("Bad Request"),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
