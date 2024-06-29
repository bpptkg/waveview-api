from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.users.serializers import UserSerializer


class AccountEndpoint(Endpoint):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id="Get Account Info",
        operation_description=(
            """
            Get user account information.
            """
        ),
        tags=["Account"],
        responses={status.HTTP_200_OK: openapi.Response("OK", UserSerializer)},
    )
    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
