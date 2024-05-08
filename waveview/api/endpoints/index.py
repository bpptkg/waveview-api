from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from waveview.api.base import Endpoint
from waveview.users.serializers import UserSerializer


class IndexEndpoint(Endpoint):
    permission_classes = []
    exclude_transform = True

    @swagger_auto_schema(auto_schema=None)
    def get(self, request: Request) -> Response:
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user)
            user = serializer.data
        else:
            user = None

        context = {"version": "1", "user": user}
        return Response(context, status=status.HTTP_200_OK)
